"""
db.py — Heritage Samarth | Database Layer
==========================================
All SQLite access goes through this module. Never import sqlite3 directly in app.py.

Tables:
  users           — login credentials and RLS scope config
  activity_log    — usage analytics (replaces analytics.json)
  login_attempts  — brute-force rate limiting

Security practices applied:
  - bcrypt password hashing (cost factor 12)
  - Login rate-limit: 5 failed attempts per email per 15 minutes → locked
  - scope_value stored as JSON text (list of SO codes, or null for ALL)
  - No plaintext passwords ever written to disk
"""
from dotenv import load_dotenv
load_dotenv()
import sqlite3
import json
import secrets
import bcrypt
from datetime import datetime, timedelta
from contextlib import contextmanager
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "samarth.db")

# ─────────────────────────────────────────────
# Rate-limit config
# ─────────────────────────────────────────────
MAX_FAILED_ATTEMPTS = 5          # allowed failures before lock
LOCKOUT_WINDOW_MINUTES = 15      # rolling window in minutes
MAX_LOG_ROWS = 10_000            # prune activity_log if it exceeds this


# ═══════════════════════════════════════════════════════════
# 1. SCHEMA INIT
# ═══════════════════════════════════════════════════════════

def init_db():
    """
    Create all tables and indexes if they don't already exist.
    Safe to call on every application start.
    """
    with _db() as conn:
        conn.executescript("""
            -- ── Users ──────────────────────────────────────────────────
            CREATE TABLE IF NOT EXISTS users (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                email        TEXT    UNIQUE NOT NULL,
                name         TEXT    NOT NULL,
                password_hash TEXT   NOT NULL,
                role         TEXT    NOT NULL,           -- 'Superadmin', 'CXO', 'RH'
                title        TEXT    DEFAULT '',
                scope_type   TEXT    DEFAULT 'ALL',      -- 'ALL' or 'SO'
                scope_value  TEXT    DEFAULT NULL,       -- JSON array e.g. '["1940","1941"]' or NULL
                is_active    INTEGER DEFAULT 1,
                created_at   TEXT    DEFAULT (datetime('now')),
                last_login   TEXT    DEFAULT NULL
            );

            -- ── Activity log ────────────────────────────────────────────
            CREATE TABLE IF NOT EXISTS activity_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp  TEXT    NOT NULL,
                email      TEXT    NOT NULL,
                role       TEXT    DEFAULT '',
                action     TEXT    NOT NULL,
                details    TEXT    DEFAULT ''
            );

            -- ── Login attempt tracker (rate limiting) ───────────────────
            CREATE TABLE IF NOT EXISTS login_attempts (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                email        TEXT    NOT NULL,
                ip_address   TEXT    DEFAULT '',
                attempted_at TEXT    DEFAULT (datetime('now')),
                success      INTEGER DEFAULT 0           -- 1 = success, 0 = failure
            );

            -- ── Password reset tokens ────────────────────────────────────
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                email      TEXT    NOT NULL,
                token      TEXT    UNIQUE NOT NULL,
                expires_at TEXT    NOT NULL,
                used       INTEGER DEFAULT 0,            -- 1 once consumed
                created_at TEXT    DEFAULT (datetime('now'))
            );

            -- ── Indexes ─────────────────────────────────────────────────
            CREATE INDEX IF NOT EXISTS idx_log_email      ON activity_log(email);
            CREATE INDEX IF NOT EXISTS idx_log_ts         ON activity_log(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_attempt_email  ON login_attempts(email);
            CREATE INDEX IF NOT EXISTS idx_attempt_time   ON login_attempts(attempted_at DESC);
            CREATE INDEX IF NOT EXISTS idx_reset_token    ON password_reset_tokens(token);
            CREATE INDEX IF NOT EXISTS idx_reset_email    ON password_reset_tokens(email);
        """)


# ═══════════════════════════════════════════════════════════
# 2. CONNECTION CONTEXT MANAGER
# ═══════════════════════════════════════════════════════════

@contextmanager
def _db():
    """
    Yields a sqlite3 connection with Row factory enabled.
    Auto-commits on success, rolls back on exception.
    WAL mode improves concurrent read performance.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════
# 3. PASSWORD UTILITIES
# ═══════════════════════════════════════════════════════════

def hash_password(plaintext: str) -> str:
    """Return a bcrypt hash string for the given plaintext password."""
    return bcrypt.hashpw(plaintext.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plaintext: str, hashed: str) -> bool:
    """Return True if plaintext matches the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plaintext.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════
# 4. RATE LIMITING
# ═══════════════════════════════════════════════════════════

def is_locked_out(email: str) -> bool:
    """
    Return True if the email has ≥ MAX_FAILED_ATTEMPTS consecutive failures
    in the last LOCKOUT_WINDOW_MINUTES minutes.
    """
    cutoff = (datetime.now() - timedelta(minutes=LOCKOUT_WINDOW_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
    with _db() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM   login_attempts
            WHERE  email        = ?
              AND  attempted_at >= ?
              AND  success      = 0
            """,
            (email, cutoff),
        ).fetchone()
    return (row["cnt"] if row else 0) >= MAX_FAILED_ATTEMPTS


def record_login_attempt(email: str, ip: str, success: bool):
    """Persist a login attempt row for rate-limit tracking."""
    with _db() as conn:
        conn.execute(
            "INSERT INTO login_attempts (email, ip_address, attempted_at, success) VALUES (?, ?, ?, ?)",
            (email, ip, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 1 if success else 0),
        )
    # Housekeeping: keep the attempts table small (keep last 30 days)
    _prune_attempts()


def _prune_attempts():
    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    with _db() as conn:
        conn.execute("DELETE FROM login_attempts WHERE attempted_at < ?", (cutoff,))


# ═══════════════════════════════════════════════════════════
# 5. USER CRUD
# ═══════════════════════════════════════════════════════════

def _row_to_user_dict(row) -> dict:
    """Convert a sqlite3.Row to a clean Python dict with scope_value decoded."""
    if row is None:
        return None
    d = dict(row)
    d["scope_value"] = json.loads(d["scope_value"]) if d.get("scope_value") else None
    return d


def get_user_by_email(email: str) -> dict | None:
    """Fetch a single user dict, or None if not found / inactive."""
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ? AND is_active = 1",
            (email,),
        ).fetchone()
    return _row_to_user_dict(row)


def get_all_users() -> dict:
    """
    Return all users as a dict keyed by email.
    Matches the shape previously returned by load_users() so admin API needs minimal changes.
    password_hash is excluded from the returned dict for safety.
    """
    with _db() as conn:
        rows = conn.execute("SELECT * FROM users WHERE is_active = 1 ORDER BY email").fetchall()
    result = {}
    for row in rows:
        d = _row_to_user_dict(row)
        email = d.pop("email")
        d.pop("password_hash", None)   # never expose hash to the frontend
        result[email] = d
    return result


def upsert_user(email: str, name: str, password: str, role: str, title: str,
                scope_type: str, scope_value) -> None:
    """
    Insert or update a user record.
    If password is blank string on update, keep the existing hash.
    scope_value may be a list (SO codes) or None.
    """
    scope_json = json.dumps(scope_value) if scope_value else None

    with _db() as conn:
        existing = conn.execute(
            "SELECT password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()

        if existing:
            # UPDATE — only re-hash if a new password was provided
            new_hash = hash_password(password) if password.strip() else existing["password_hash"]
            conn.execute(
                """
                UPDATE users
                SET    name        = ?,
                       password_hash = ?,
                       role        = ?,
                       title       = ?,
                       scope_type  = ?,
                       scope_value = ?,
                       is_active   = 1
                WHERE  email       = ?
                """,
                (name, new_hash, role, title, scope_type, scope_json, email),
            )
        else:
            # INSERT — password is required
            if not password.strip():
                raise ValueError("Password is required when creating a new user.")
            conn.execute(
                """
                INSERT INTO users (email, name, password_hash, role, title, scope_type, scope_value)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (email, name, hash_password(password), role, title, scope_type, scope_json),
            )


def delete_user(email: str) -> bool:
    """Soft-delete a user (sets is_active=0). Returns True if the user existed."""
    with _db() as conn:
        cur = conn.execute(
            "UPDATE users SET is_active = 0 WHERE email = ? AND role != 'Superadmin'",
            (email,),
        )
    return cur.rowcount > 0


def touch_last_login(email: str):
    """Update last_login timestamp for a user."""
    with _db() as conn:
        conn.execute(
            "UPDATE users SET last_login = ? WHERE email = ?",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), email),
        )


def change_password(email: str, new_password: str) -> None:
    """Update password hash for a user."""
    with _db() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE email = ?",
            (hash_password(new_password), email),
        )


# ═══════════════════════════════════════════════════════════
# 6. ACTIVITY LOG
# ═══════════════════════════════════════════════════════════

def log_activity(email: str, role: str, action: str, details: str = "") -> None:
    """
    Insert one activity-log row and prune if total exceeds MAX_LOG_ROWS.
    Thread-safe via WAL mode.
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _db() as conn:
        conn.execute(
            "INSERT INTO activity_log (timestamp, email, role, action, details) VALUES (?, ?, ?, ?, ?)",
            (ts, email, role, action, details),
        )
        # Prune: keep only the most recent MAX_LOG_ROWS rows
        count = conn.execute("SELECT COUNT(*) FROM activity_log").fetchone()[0]
        if count > MAX_LOG_ROWS:
            conn.execute(
                """
                DELETE FROM activity_log
                WHERE id IN (
                    SELECT id FROM activity_log
                    ORDER BY id ASC
                    LIMIT ?
                )
                """,
                (count - MAX_LOG_ROWS,),
            )


def get_activity_log(limit: int = 10_000) -> list[dict]:
    """
    Fetch recent activity-log rows as a list of dicts.
    Returned newest-first to match the previous analytics.json ordering.
    """
    with _db() as conn:
        rows = conn.execute(
            "SELECT timestamp, email, role, action, details FROM activity_log ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


# ═══════════════════════════════════════════════════════════
# 8. PASSWORD RESET TOKENS
# ═══════════════════════════════════════════════════════════

RESET_TOKEN_EXPIRY_MINUTES = 60    # tokens expire after 1 hour
RESET_RATE_LIMIT_MINUTES   = 5     # minimum gap between reset requests per email


def can_request_reset(email: str) -> bool:
    """
    Return True if the user hasn't requested a reset token in the last
    RESET_RATE_LIMIT_MINUTES minutes. Prevents reset-email spam.
    """
    cutoff = (datetime.now() - timedelta(minutes=RESET_RATE_LIMIT_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
    with _db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM password_reset_tokens WHERE email = ? AND created_at >= ?",
            (email, cutoff),
        ).fetchone()
    return (row["cnt"] if row else 0) == 0


def create_reset_token(email: str) -> str:
    """
    Generate a cryptographically secure URL-safe token, store it in the DB
    with a 1-hour expiry, and return the raw token string.

    Any previously unused tokens for this email are invalidated first
    so only one active token exists per user at a time.
    """
    # Invalidate old pending tokens
    with _db() as conn:
        conn.execute(
            "UPDATE password_reset_tokens SET used = 1 WHERE email = ? AND used = 0",
            (email,),
        )

    token      = secrets.token_urlsafe(48)   # 48 bytes → 64-char URL-safe string
    expires_at = (datetime.now() + timedelta(minutes=RESET_TOKEN_EXPIRY_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")

    with _db() as conn:
        conn.execute(
            "INSERT INTO password_reset_tokens (email, token, expires_at) VALUES (?, ?, ?)",
            (email, token, expires_at),
        )

    return token


def validate_reset_token(token: str) -> str | None:
    """
    Check that the token exists, hasn't been used, and hasn't expired.
    Returns the associated email on success, or None on any failure.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _db() as conn:
        row = conn.execute(
            """
            SELECT email FROM password_reset_tokens
            WHERE  token      = ?
              AND  used        = 0
              AND  expires_at >= ?
            """,
            (token, now),
        ).fetchone()
    return row["email"] if row else None


def consume_reset_token(token: str, new_password: str) -> bool:
    """
    Validate the token, update the user's password, and mark the token as used.
    Returns True on success, False if the token is invalid/expired.
    All three steps happen in a single transaction.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _db() as conn:
        row = conn.execute(
            """
            SELECT id, email FROM password_reset_tokens
            WHERE  token      = ?
              AND  used        = 0
              AND  expires_at >= ?
            """,
            (token, now),
        ).fetchone()

        if not row:
            return False

        new_hash = hash_password(new_password)

        conn.execute(
            "UPDATE users SET password_hash = ? WHERE email = ?",
            (new_hash, row["email"]),
        )
        conn.execute(
            "UPDATE password_reset_tokens SET used = 1 WHERE id = ?",
            (row["id"],),
        )

    return True


def prune_expired_tokens():
    """
    Delete tokens older than 24 hours. Call occasionally to keep the table small.
    """
    cutoff = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    with _db() as conn:
        conn.execute(
            "DELETE FROM password_reset_tokens WHERE expires_at < ?",
            (cutoff,),
        )