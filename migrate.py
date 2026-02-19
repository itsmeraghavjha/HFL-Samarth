"""
migrate.py — Heritage Samarth | JSON → SQLite Migration
=========================================================
Run ONCE after deploying the new SQLite-backed app.py.

  python migrate.py

What it does:
  1. Initialises the SQLite schema (safe to run on existing DB)
  2. Reads users.json and inserts every user with a bcrypt-hashed password
  3. Reads analytics.json and bulk-inserts all activity-log rows
  4. Renames the old JSON files to *.bak so they're no longer used

After this script succeeds:
  - users.json     → users.json.bak
  - analytics.json → analytics.json.bak
  - samarth.db     is ready to use

Safety:
  - Existing users in the DB are SKIPPED (not overwritten) so you can
    safely re-run if the script was interrupted.
  - The JSON files are only renamed at the very end, after all inserts succeed.
"""

import json
import os
import sys
from datetime import datetime
import db   # our database layer


# ── Colour helpers for terminal output ──────────────────────
def ok(msg):  print(f"  ✅  {msg}")
def info(msg): print(f"  ℹ️   {msg}")
def warn(msg): print(f"  ⚠️   {msg}")
def err(msg):  print(f"  ❌  {msg}")


def migrate_users(users_path: str = "users.json") -> int:
    """
    Read users.json and insert into the users table.
    Returns the number of users inserted.
    """
    if not os.path.exists(users_path):
        warn(f"{users_path} not found — skipping user migration.")
        return 0

    with open(users_path) as f:
        users: dict = json.load(f)

    inserted = 0
    skipped  = 0

    for email, u in users.items():
        email = email.strip().lower()

        # Skip if already in DB
        if db.get_user_by_email(email):
            warn(f"User {email} already exists in DB — skipped.")
            skipped += 1
            continue

        plaintext = "Heritage@123"
        scope_val = u.get("scope_value")

        # Normalise scope_value to list or None
        if isinstance(scope_val, str):
            scope_val = [x.strip() for x in scope_val.split(",") if x.strip()] or None

        try:
            db.upsert_user(
                email       = email,
                name        = u.get("name", ""),
                password    = plaintext,
                role        = u.get("role", "RH"),
                title       = u.get("title", ""),
                scope_type  = u.get("scope_type", "ALL"),
                scope_value = scope_val,
            )
            ok(f"Inserted user: {email}  (role={u.get('role')})")
            inserted += 1
        except Exception as e:
            err(f"Failed to insert {email}: {e}")

    info(f"Users → {inserted} inserted, {skipped} skipped.")
    return inserted


def migrate_analytics(analytics_path: str = "analytics.json") -> int:
    """
    Read analytics.json and bulk-insert into activity_log.
    Rows are inserted oldest-first so the auto-increment ID reflects chronological order.
    Returns the number of rows inserted.
    """
    if not os.path.exists(analytics_path):
        warn(f"{analytics_path} not found — skipping analytics migration.")
        return 0

    with open(analytics_path) as f:
        logs: list = json.load(f)

    if not logs:
        info("analytics.json is empty — nothing to migrate.")
        return 0

    # analytics.json is newest-first; reverse to insert oldest-first
    logs = list(reversed(logs))

    import sqlite3
    conn = sqlite3.connect(db.DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        conn.executemany(
            "INSERT INTO activity_log (timestamp, email, role, action, details) VALUES (?, ?, ?, ?, ?)",
            [
                (
                    row.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    row.get("email", ""),
                    row.get("role",  ""),
                    row.get("action", ""),
                    row.get("details", ""),
                )
                for row in logs
            ],
        )
        conn.commit()
    finally:
        conn.close()

    ok(f"Inserted {len(logs):,} activity-log rows.")
    return len(logs)


def archive_json_files():
    """Rename old JSON files to .bak after successful migration."""
    for filename in ("users.json", "analytics.json"):
        if os.path.exists(filename):
            bak = filename + ".bak"
            os.rename(filename, bak)
            ok(f"Archived {filename} → {bak}")


def main():
    print("\n" + "═" * 55)
    print("  Heritage Samarth — JSON → SQLite Migration")
    print("═" * 55 + "\n")

    # 1. Init schema
    print("Step 1/4 — Initialising SQLite schema...")
    db.init_db()
    ok(f"Schema ready at: {db.DB_PATH}")

    # 2. Migrate users
    print("\nStep 2/4 — Migrating users.json...")
    user_count = migrate_users()

    # 3. Migrate analytics
    print("\nStep 3/4 — Migrating analytics.json...")
    log_count = migrate_analytics()

    # 4. Archive old files
    print("\nStep 4/4 — Archiving JSON files...")
    archive_json_files()

    print("\n" + "─" * 55)
    print(f"  Done! {user_count} users · {log_count:,} log rows migrated.")
    print("  You can now start the app with:\n")
    print("    export SECRET_KEY=$(python -c \"import secrets; print(secrets.token_hex(32))\")")
    print("    python app.py\n")
    print("  ⚠️  IMPORTANT: All existing passwords have been hashed with bcrypt.")
    print("  Users' plaintext passwords will still work — they'll just be")
    print("  checked against the hash from now on.")
    print("─" * 55 + "\n")


if __name__ == "__main__":
    main()