# import os
# import json
# import time
# import pyodbc
# from decimal import Decimal
# from datetime import date, datetime, timedelta
# from flask import Flask, render_template, jsonify, request, session, redirect, url_for
# from functools import wraps

# app = Flask(__name__, static_folder='static')

# # ==========================================
# # 1. SECURITY & CONFIGURATION
# # ==========================================
# app.secret_key = os.environ.get('SECRET_KEY', 'Heritage_Samarth_Secure_Key_2024')
# USERS_FILE = 'users.json'
# ANALYTICS_FILE = 'analytics.json'

# class Config:
#     DB_SERVER = '10.0.1.71,4000'
#     DB_NAME = 'HeritageBI'
#     DB_USER = '127903'
#     DB_PASS = 'Raghavkumar.j@heritagefoods.in'

#     # ─────────────────────────────────────────────────────────────
#     # CACHE STRATEGY: Daily 9 AM Window
#     #
#     # The database refreshes overnight (typically 2–5 AM).
#     # We want to load fresh data ONCE at/after 9 AM each morning,
#     # then serve that same snapshot to all users for the full day.
#     #
#     # Rule: The cache is considered VALID if it was populated
#     # after today's 9:00:00 AM. Before 9 AM, the previous day's
#     # cache (loaded after yesterday's 9 AM) is still valid.
#     #
#     # This means:
#     #   - First request at or after 9 AM → triggers a DB fetch
#     #   - All subsequent requests that day → served from cache
#     #   - No TTL countdown — cache is date-window based, not time-delta based
#     # ─────────────────────────────────────────────────────────────
#     CACHE_HOUR = 9   # 9 AM — change this if your DB refresh time shifts


# DATA_CACHE = {
#     "timestamp": 0,       # epoch float of when cache was last populated
#     "columns": [],
#     "data": [],
#     "column_map": {}
# }


# # ==========================================
# # 2. CACHE WINDOW LOGIC
# # ==========================================

# def get_cache_window_start():
#     """
#     Returns the datetime of the most recent 9 AM cutoff.

#     Logic:
#       - If current time is 9:00 AM or later today  → return today @ 9:00:00
#       - If current time is before 9:00 AM today    → return yesterday @ 9:00:00

#     This means the "valid window" is always:
#         [most_recent_9am, next_9am)

#     Example timeline:
#         08:55 AM today  → window start = yesterday 9:00 AM
#         09:01 AM today  → window start = today 9:00 AM
#         11:59 PM today  → window start = today 9:00 AM
#     """
#     now = datetime.now()
#     today_9am = now.replace(hour=Config.CACHE_HOUR, minute=0, second=0, microsecond=0)

#     if now >= today_9am:
#         return today_9am
#     else:
#         return today_9am - timedelta(days=1)


# def cache_is_fresh():
#     """
#     Returns True if the cache was populated within the current 9 AM window.
#     Returns False if:
#       - Cache is empty (first ever run)
#       - Cache was loaded before today's 9 AM (i.e., it's stale from yesterday or older)
#     """
#     if not DATA_CACHE['data'] or DATA_CACHE['timestamp'] == 0:
#         return False

#     cache_loaded_at = datetime.fromtimestamp(DATA_CACHE['timestamp'])
#     window_start = get_cache_window_start()

#     return cache_loaded_at >= window_start


# def next_cache_refresh():
#     """
#     Returns the datetime of the next scheduled cache refresh (next 9 AM).
#     Used for display in the UI header.
#     """
#     now = datetime.now()
#     today_9am = now.replace(hour=Config.CACHE_HOUR, minute=0, second=0, microsecond=0)

#     if now < today_9am:
#         return today_9am                       # today's 9 AM hasn't happened yet
#     else:
#         return today_9am + timedelta(days=1)   # tomorrow's 9 AM


# # ==========================================
# # 3. HELPER FUNCTIONS
# # ==========================================

# def load_users():
#     if not os.path.exists(USERS_FILE): return {}
#     with open(USERS_FILE, 'r') as f: return json.load(f)

# def save_users(users_dict):
#     with open(USERS_FILE, 'w') as f: json.dump(users_dict, f, indent=4)

# def log_activity(email, role, action, details):
#     """Logs user activity to a local JSON file for the Admin Dashboard."""
#     logs = []
#     if os.path.exists(ANALYTICS_FILE):
#         try:
#             with open(ANALYTICS_FILE, 'r') as f: logs = json.load(f)
#         except: pass

#     logs.insert(0, {
#         "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#         "email": email,
#         "role": role,
#         "action": action,
#         "details": details
#     })

#     with open(ANALYTICS_FILE, 'w') as f:
#         json.dump(logs[:10000], f, indent=4)

# def login_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if 'user' not in session: return redirect(url_for('login'))
#         return f(*args, **kwargs)
#     return decorated_function

# def superadmin_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if 'user' not in session or session['user'].get('role') != 'Superadmin':
#             return redirect(url_for('dashboard'))
#         return f(*args, **kwargs)
#     return decorated_function

# def get_db_connection():
#     driver = '{ODBC Driver 17 for SQL Server}'
#     conn_str = (
#         f'DRIVER={driver};SERVER={Config.DB_SERVER};'
#         f'DATABASE={Config.DB_NAME};UID={Config.DB_USER};PWD={Config.DB_PASS}'
#     )
#     return pyodbc.connect(conn_str)


# def refresh_data(force=False):
#     """
#     Loads data from DB into DATA_CACHE.

#     Normal call:  refresh_data()
#       → Only fetches if cache is stale (outside current 9 AM window)

#     Force call:   refresh_data(force=True)
#       → Always fetches, regardless of cache state.
#       → Used by the /api/refresh endpoint (Superadmin only).
#     """
#     global DATA_CACHE

#     # Skip fetch if cache is still fresh — UNLESS force=True
#     if not force and cache_is_fresh():
#         return

#     print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Fetching fresh data from DB...")

#     try:
#         with open('SQLQuery_performance_analysis.sql', 'r') as f:
#             sql_query = f.read()

#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute(sql_query)

#         columns = [column[0] for column in cursor.description]
#         formatted_data = []

#         for row in cursor.fetchall():
#             clean_row = []
#             for val in row:
#                 if val is None:
#                     clean_row.append("")
#                 elif isinstance(val, Decimal):
#                     clean_row.append(float(val))
#                 elif isinstance(val, (date, datetime)):
#                     clean_row.append(val.strftime("%Y-%m-%d"))
#                 else:
#                     clean_row.append(val)
#             formatted_data.append(clean_row)

#         conn.close()

#         DATA_CACHE.update({
#             "timestamp": time.time(),
#             "columns": columns,
#             "data": formatted_data,
#             "column_map": {name: i for i, name in enumerate(columns)}
#         })

#         print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Cache populated — {len(formatted_data):,} rows. Valid until {next_cache_refresh().strftime('%d %b %Y, %I:%M %p')}.")

#     except Exception as e:
#         print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ DB Error: {e}")


# # ==========================================
# # 4. AUTH & MAIN ROUTES
# # ==========================================

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     error = None
#     if request.method == 'POST':
#         email = request.form.get('email')
#         password = request.form.get('password')
#         users = load_users()
#         user = users.get(email)

#         if user and user['password'] == password:
#             user['email'] = email
#             session['user'] = user
#             log_activity(email, user['role'], "Login", "User authenticated")

#             if user['role'] == 'Superadmin': return redirect(url_for('admin_panel'))
#             return redirect(url_for('dashboard'))
#         else:
#             error = 'Invalid credentials. Please try again.'

#     return render_template('login.html', error=error)

# @app.route('/logout')
# def logout():
#     if 'user' in session:
#         log_activity(session['user']['email'], session['user']['role'], "Logout", "User signed out manually")
#     session.pop('user', None)
#     return redirect(url_for('login'))

# @app.route('/')
# @login_required
# def dashboard():
#     return render_template('dashboard.html', user=session['user'])


# # ==========================================
# # 5. API & DATA ENDPOINTS
# # ==========================================

# @app.route('/api/data')
# @login_required
# def api_data():
#     refresh_data()   # No-op if cache is fresh; fetches if stale

#     current_user = session['user']
#     columns = list(DATA_CACHE['columns'])
#     data = list(DATA_CACHE['data'])
#     col_map = DATA_CACHE['column_map']

#     # Row-Level Security filtering
#     if current_user.get('scope_type') == 'SO':
#         if 'SO' in col_map:
#             scope_idx = col_map['SO']
#             allowed_sos = set(current_user['scope_value'])
#             data = [
#                 row for row in data
#                 if row[scope_idx] is not None
#                 and str(row[scope_idx]).replace('.0', '').strip() in allowed_sos
#             ]

#     elif current_user.get('scope_type') not in ['ALL', None, '']:
#         scope_col = current_user['scope_type']
#         scope_val = current_user['scope_value']
#         if scope_col in col_map:
#             scope_idx = col_map[scope_col]
#             data = [
#                 row for row in data
#                 if str(row[scope_idx]).strip() == str(scope_val).strip()
#             ]

#     # Build cache metadata for UI display
#     cache_loaded_at = (
#         datetime.fromtimestamp(DATA_CACHE['timestamp']).strftime('%d %b, %I:%M %p')
#         if DATA_CACHE['timestamp'] else "Never"
#     )
#     next_refresh = next_cache_refresh().strftime('%d %b, %I:%M %p')

#     return jsonify({
#         "data": data,
#         "columns": [{"title": c} for c in columns],
#         "last_updated": cache_loaded_at,
#         "next_refresh": next_refresh,             # NEW — shown in dashboard header
#         "cache_fresh": cache_is_fresh(),          # NEW — used for stale-data banner logic
#         "row_count": len(DATA_CACHE['data'])      # NEW — total rows before RLS filter
#     })


# @app.route('/api/track', methods=['POST'])
# @login_required
# def track_usage():
#     data = request.json
#     log_activity(
#         session['user']['email'],
#         session['user']['role'],
#         data.get('action'),
#         data.get('details')
#     )
#     return jsonify({"status": "tracked"})


# @app.route('/api/refresh', methods=['POST'])
# @login_required
# @superadmin_required
# def force_refresh():
#     """
#     Superadmin-only endpoint to force a DB re-fetch outside the 9 AM schedule.
#     Useful after an emergency DB reload or data correction.
#     Logs the action for audit trail.
#     """
#     log_activity(
#         session['user']['email'],
#         session['user']['role'],
#         "Force Refresh",
#         f"Superadmin triggered manual cache refresh"
#     )

#     refresh_data(force=True)

#     return jsonify({
#         "status": "refreshed",
#         "last_updated": datetime.fromtimestamp(DATA_CACHE['timestamp']).strftime('%d %b, %I:%M %p'),
#         "next_refresh": next_cache_refresh().strftime('%d %b, %I:%M %p'),
#         "row_count": len(DATA_CACHE['data'])
#     })


# # ==========================================
# # 6. SUPERADMIN ROUTES
# # ==========================================

# @app.route('/admin')
# @superadmin_required
# def admin_panel():
#     return render_template('admin.html', user=session['user'])

# @app.route('/api/users', methods=['GET', 'POST', 'PUT', 'DELETE'])
# @superadmin_required
# def manage_users():
#     users = load_users()
#     if request.method == 'GET': return jsonify(users)

#     if request.method in ['POST', 'PUT']:
#         data = request.json
#         email = data.get('email')
#         scope_val = data.get('scope_value')
#         if data.get('scope_type') == 'SO' and isinstance(scope_val, str):
#             scope_val = [x.strip() for x in scope_val.split(',') if x.strip()]

#         users[email] = {
#             "password": data.get('password'),
#             "name": data.get('name'),
#             "role": data.get('role'),
#             "title": data.get('title'),
#             "scope_type": data.get('scope_type'),
#             "scope_value": scope_val
#         }
#         save_users(users)
#         return jsonify({"message": "User saved"})

#     if request.method == 'DELETE':
#         email = request.json.get('email')
#         if email in users:
#             del users[email]
#             save_users(users)
#             return jsonify({"message": "User deleted"})
#         return jsonify({"error": "User not found"}), 404

# @app.route('/api/analytics')
# @superadmin_required
# def get_analytics():
#     if not os.path.exists(ANALYTICS_FILE): return jsonify([])
#     try:
#         with open(ANALYTICS_FILE, 'r') as f: return jsonify(json.load(f))
#     except:
#         return jsonify([])

# @app.route('/api/cache-status')
# @superadmin_required
# def cache_status():
#     """
#     Returns current cache state for the admin panel to display.
#     """
#     return jsonify({
#         "is_fresh": cache_is_fresh(),
#         "loaded_at": datetime.fromtimestamp(DATA_CACHE['timestamp']).strftime('%d %b %Y, %I:%M:%S %p') if DATA_CACHE['timestamp'] else "Never loaded",
#         "window_start": get_cache_window_start().strftime('%d %b %Y, %I:%M %p'),
#         "next_refresh": next_cache_refresh().strftime('%d %b %Y, %I:%M %p'),
#         "row_count": len(DATA_CACHE['data']),
#         "cache_hour": Config.CACHE_HOUR
#     })


# if __name__ == '__main__':
#     print("\n🚀 Heritage Samarth System is Running!")
#     print(f"📅 Cache strategy: Daily window from {Config.CACHE_HOUR}:00 AM")
#     print(f"⏰ Next cache load: {next_cache_refresh().strftime('%d %b %Y, %I:%M %p')}\n")
#     app.run(debug=True, host='0.0.0.0', port=5000)


"""
app.py — Heritage Samarth Analytics Engine
===========================================
Auth and data API backed by SQLite (see db.py).
Passwords are bcrypt-hashed. Login is rate-limited.
"""

import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from decimal import Decimal
from datetime import date, datetime, timedelta

from flask import (
    Flask, render_template, jsonify, request,
    session, redirect, url_for, abort, flash,
)
from functools import wraps
from dotenv import load_dotenv

load_dotenv()   # reads .env into os.environ before anything else runs

import db   # ← our SQLite layer

app = Flask(__name__, static_folder="static")

# ══════════════════════════════════════════════════════════════
# 1. CONFIGURATION
# ══════════════════════════════════════════════════════════════

app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError(
        "SECRET_KEY environment variable is not set. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )

# Session hardening
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,    # JS cannot read the cookie
    SESSION_COOKIE_SAMESITE="Lax",  # CSRF mitigation
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
)

# ─────────────────────────────────────────────────────────────
# CACHE STRATEGY: Daily 9 AM Window
#
# The database refreshes overnight (typically 2–5 AM).
# We load fresh data ONCE at/after 9 AM each morning,
# then serve that snapshot to all users for the full day.
# ─────────────────────────────────────────────────────────────

class Config:
    DB_SERVER  = os.environ.get("MSSQL_SERVER", "10.0.1.71,4000")
    DB_NAME    = os.environ.get("MSSQL_DB",     "HeritageBI")
    DB_USER    = os.environ.get("MSSQL_USER",   "127903")
    DB_PASS    = os.environ.get("MSSQL_PASS",   "")
    CACHE_HOUR = int(os.environ.get("CACHE_HOUR", "9"))

    # SMTP — set these in .env
    SMTP_HOST     = os.environ.get("SMTP_HOST",     "smtp.gmail.com")
    SMTP_PORT     = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER     = os.environ.get("SMTP_USER",     "")
    SMTP_PASS     = os.environ.get("SMTP_PASS",     "")
    SMTP_FROM     = os.environ.get("SMTP_FROM",     "Samarth Analytics <noreply@heritagefoods.in>")
    APP_BASE_URL  = os.environ.get("APP_BASE_URL",  "http://localhost:5000")


# ── Email helper ─────────────────────────────────────────────────────────────

def send_reset_email(to_email: str, token: str) -> tuple[bool, str]:
    """
    Send a password-reset link to the user.
    Returns (success: bool, error_message: str).

    The reset link embeds the token as a URL query parameter and expires
    after db.RESET_TOKEN_EXPIRY_MINUTES minutes (default 60).
    """
    if not Config.SMTP_USER or not Config.SMTP_PASS:
        return False, "SMTP credentials are not configured in .env"

    reset_url  = f"{Config.APP_BASE_URL}/reset-password?token={token}"
    expiry_min = db.RESET_TOKEN_EXPIRY_MINUTES

    # ── Plain-text body ───────────────────────────────────────
    text_body = f"""Hello,

You requested a password reset for your Heritage Samarth account.

Click the link below to set a new password (valid for {expiry_min} minutes):

  {reset_url}

If you did not request this, please ignore this email — your password will not change.

— Heritage Samarth System
"""

    # ── HTML body ─────────────────────────────────────────────
    html_body = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#F8FAFC;font-family:Inter,Arial,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:40px 20px">
      <table width="520" cellpadding="0" cellspacing="0"
             style="background:white;border-radius:16px;overflow:hidden;
                    box-shadow:0 4px 24px rgba(0,0,0,0.08)">
        <!-- Header -->
        <tr><td style="background:#2E963D;padding:28px 36px">
          <h1 style="margin:0;color:white;font-size:20px;font-weight:800;
                     letter-spacing:-0.5px">Heritage Samarth</h1>
          <p style="margin:4px 0 0;color:#BBFFD6;font-size:12px;
                    font-weight:600;letter-spacing:1px;text-transform:uppercase">
            Analytics Engine
          </p>
        </td></tr>
        <!-- Body -->
        <tr><td style="padding:36px">
          <h2 style="margin:0 0 12px;color:#111827;font-size:18px">
            Password Reset Request
          </h2>
          <p style="margin:0 0 24px;color:#6B7280;font-size:14px;line-height:1.6">
            We received a request to reset the password for your account.
            Click the button below to choose a new password. This link
            expires in <strong>{expiry_min} minutes</strong>.
          </p>
          <a href="{reset_url}"
             style="display:inline-block;background:#2E963D;color:white;
                    padding:14px 32px;border-radius:10px;font-weight:700;
                    font-size:14px;text-decoration:none;letter-spacing:0.2px">
            Reset My Password →
          </a>
          <p style="margin:24px 0 0;color:#9CA3AF;font-size:12px;line-height:1.6">
            If the button doesn't work, copy and paste this link into your browser:<br>
            <a href="{reset_url}" style="color:#2E963D;word-break:break-all">{reset_url}</a>
          </p>
          <hr style="margin:28px 0;border:none;border-top:1px solid #F1F5F9">
          <p style="margin:0;color:#D1D5DB;font-size:11px">
            If you didn't request a password reset, you can safely ignore this email.
            Your password will remain unchanged.
          </p>
        </td></tr>
        <!-- Footer -->
        <tr><td style="background:#F9FAFB;padding:16px 36px;border-top:1px solid #F1F5F9">
          <p style="margin:0;color:#9CA3AF;font-size:11px">
            Heritage Foods Limited · Samarth Analytics Platform
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    try:
        msg                    = MIMEMultipart("alternative")
        msg["Subject"]         = "Reset your Samarth password"
        msg["From"]            = Config.SMTP_FROM
        msg["To"]              = to_email
        msg["X-Mailer"]        = "Heritage-Samarth/2.0"

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(Config.SMTP_USER, Config.SMTP_PASS)
            server.sendmail(Config.SMTP_FROM, to_email, msg.as_string())

        return True, ""

    except smtplib.SMTPAuthenticationError:
        return False, "SMTP authentication failed — check SMTP_USER and SMTP_PASS in .env"
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {e}"
    except Exception as e:
        return False, f"Unexpected error sending email: {e}"


DATA_CACHE = {
    "timestamp": 0,
    "columns": [],
    "data": [],
    "column_map": {},
}


# ══════════════════════════════════════════════════════════════
# 2. CACHE WINDOW HELPERS
# ══════════════════════════════════════════════════════════════

def get_cache_window_start() -> datetime:
    now = datetime.now()
    today_9am = now.replace(hour=Config.CACHE_HOUR, minute=0, second=0, microsecond=0)
    return today_9am if now >= today_9am else today_9am - timedelta(days=1)


def cache_is_fresh() -> bool:
    if not DATA_CACHE["data"] or DATA_CACHE["timestamp"] == 0:
        return False
    return datetime.fromtimestamp(DATA_CACHE["timestamp"]) >= get_cache_window_start()


def next_cache_refresh() -> datetime:
    now = datetime.now()
    today_9am = now.replace(hour=Config.CACHE_HOUR, minute=0, second=0, microsecond=0)
    return today_9am if now < today_9am else today_9am + timedelta(days=1)


# ══════════════════════════════════════════════════════════════
# 3. AUTH DECORATORS
# ══════════════════════════════════════════════════════════════

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def superadmin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session or session["user"].get("role") != "Superadmin":
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ══════════════════════════════════════════════════════════════
# 4. DATA LAYER (MSSQL + CACHE)
# ══════════════════════════════════════════════════════════════

def get_mssql_connection():
    import pyodbc
    driver = "{ODBC Driver 17 for SQL Server}"
    conn_str = (
        f"DRIVER={driver};SERVER={Config.DB_SERVER};"
        f"DATABASE={Config.DB_NAME};UID={Config.DB_USER};PWD={Config.DB_PASS}"
    )
    return pyodbc.connect(conn_str)


def refresh_data(force: bool = False):
    global DATA_CACHE
    if not force and cache_is_fresh():
        return

    print(f"[{datetime.now():%H:%M:%S}] 🔄 Fetching fresh data from MSSQL...")
    try:
        with open("SQLQuery_performance_analysis.sql") as f:
            sql = f.read()

        conn   = get_mssql_connection()
        cursor = conn.cursor()
        cursor.execute(sql)

        columns      = [col[0] for col in cursor.description]
        formatted    = []

        for row in cursor.fetchall():
            clean = []
            for val in row:
                if val is None:
                    clean.append("")
                elif isinstance(val, Decimal):
                    clean.append(float(val))
                elif isinstance(val, (date, datetime)):
                    clean.append(val.strftime("%Y-%m-%d"))
                else:
                    clean.append(val)
            formatted.append(clean)

        conn.close()

        DATA_CACHE.update({
            "timestamp":  time.time(),
            "columns":    columns,
            "data":       formatted,
            "column_map": {name: i for i, name in enumerate(columns)},
        })

        print(
            f"[{datetime.now():%H:%M:%S}] ✅ Cache ready — "
            f"{len(formatted):,} rows. Next refresh: "
            f"{next_cache_refresh():%d %b %Y, %I:%M %p}"
        )

    except Exception as e:
        print(f"[{datetime.now():%H:%M:%S}] ❌ DB Error: {e}")


# ══════════════════════════════════════════════════════════════
# 5. AUTH ROUTES
# ══════════════════════════════════════════════════════════════

@app.route("/login", methods=["GET", "POST"])
def login():
    # Redirect already-logged-in users
    if "user" in session:
        return redirect(url_for("dashboard"))

    error = None

    if request.method == "POST":
        email    = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        ip       = request.remote_addr

        # ── Rate limit check ────────────────────────────────────
        if db.is_locked_out(email):
            error = (
                f"Too many failed attempts. "
                f"Please wait {db.LOCKOUT_WINDOW_MINUTES} minutes before trying again."
            )
            return render_template("login.html", error=error)

        # ── Credential check ────────────────────────────────────
        user = db.get_user_by_email(email)

        if user and db.verify_password(password, user["password_hash"]):
            db.record_login_attempt(email, ip, success=True)
            db.touch_last_login(email)

            # Store only safe fields in session (no hash)
            session.permanent = True
            session["user"] = {
                "email":       email,
                "name":        user["name"],
                "role":        user["role"],
                "title":       user["title"],
                "scope_type":  user["scope_type"],
                "scope_value": user["scope_value"],
            }

            db.log_activity(email, user["role"], "Login", "User authenticated")

            if user["role"] == "Superadmin":
                return redirect(url_for("admin_panel"))
            return redirect(url_for("dashboard"))

        else:
            db.record_login_attempt(email, ip, success=False)
            # Deliberately vague — don't reveal whether email exists
            error = "Invalid credentials. Please try again."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    if "user" in session:
        u = session["user"]
        db.log_activity(u["email"], u["role"], "Logout", "User signed out manually")
    session.clear()
    return redirect(url_for("login"))


# ── Forgot Password ───────────────────────────────────────────────────────────

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """
    Step 1: User submits their email address.

    Security notes:
    - We always show the same success message whether or not the email exists.
      This prevents account enumeration (an attacker learning which emails
      are registered by watching which get the "check your inbox" response).
    - Rate-limited to one request per email per 5 minutes.
    """
    if "user" in session:
        return redirect(url_for("dashboard"))

    message = None
    error   = None

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()

        if not email:
            error = "Please enter your email address."
        else:
            user = db.get_user_by_email(email)

            if user and db.can_request_reset(email):
                token   = db.create_reset_token(email)
                ok, err = send_reset_email(email, token)

                if not ok:
                    # Log the SMTP failure server-side but don't expose details to user
                    print(f"[RESET EMAIL FAILED] {email}: {err}")

            # Always show the same message — do NOT reveal whether email exists
            message = "If that email is registered, you'll receive a reset link shortly. Check your inbox (and spam folder)."

    return render_template("forgot_password.html", message=message, error=error)


# ── Reset Password ────────────────────────────────────────────────────────────

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    """
    Step 2: User arrives via the emailed link and sets a new password.
    The token is validated on GET (to show an error early) and again on POST
    (inside the DB transaction) to prevent race conditions.
    """
    if "user" in session:
        return redirect(url_for("dashboard"))

    token = request.args.get("token") or request.form.get("token") or ""
    error = None

    # ── GET: pre-validate token so we can show "link expired" immediately ──
    if request.method == "GET":
        if not token or not db.validate_reset_token(token):
            return render_template(
                "reset_password.html",
                token=token,
                token_invalid=True,
                error=None,
            )
        return render_template("reset_password.html", token=token, token_invalid=False, error=None)

    # ── POST: apply new password ──────────────────────────────────────────
    password  = request.form.get("password", "")
    password2 = request.form.get("password2", "")

    if not password or len(password) < 8:
        error = "Password must be at least 8 characters."
    elif password != password2:
        error = "Passwords do not match."
    else:
        email = db.validate_reset_token(token)
        if not email:
            return render_template(
                "reset_password.html",
                token=token,
                token_invalid=True,
                error=None,
            )

        success = db.consume_reset_token(token, password)
        if success:
            db.log_activity(email, "", "Password Reset", "User reset password via email link")
            db.prune_expired_tokens()
            return render_template("reset_password.html", token="", token_invalid=False, success=True, error=None)
        else:
            error = "This reset link has already been used or has expired. Please request a new one."

    return render_template("reset_password.html", token=token, token_invalid=False, error=error)


@app.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html", user=session["user"])


# ══════════════════════════════════════════════════════════════
# 6. DATA API
# ══════════════════════════════════════════════════════════════

@app.route("/api/data")
@login_required
def api_data():
    refresh_data()

    current_user = session["user"]
    columns      = list(DATA_CACHE["columns"])
    data         = list(DATA_CACHE["data"])
    col_map      = DATA_CACHE["column_map"]

    # ── Row-Level Security ───────────────────────────────────
    if current_user.get("scope_type") == "SO":
        if "SO" in col_map:
            scope_idx   = col_map["SO"]
            allowed_sos = set(str(v) for v in (current_user["scope_value"] or []))
            data = [
                row for row in data
                if str(row[scope_idx]).replace(".0", "").strip() in allowed_sos
            ]

    elif current_user.get("scope_type") not in ["ALL", None, ""]:
        scope_col = current_user["scope_type"]
        scope_val = current_user["scope_value"]
        if scope_col in col_map:
            scope_idx = col_map[scope_col]
            data = [
                row for row in data
                if str(row[scope_idx]).strip() == str(scope_val).strip()
            ]

    cache_loaded_at = (
        datetime.fromtimestamp(DATA_CACHE["timestamp"]).strftime("%d %b, %I:%M %p")
        if DATA_CACHE["timestamp"] else "Never"
    )

    return jsonify({
        "data":         data,
        "columns":      [{"title": c} for c in columns],
        "last_updated": cache_loaded_at,
        "next_refresh": next_cache_refresh().strftime("%d %b, %I:%M %p"),
        "cache_fresh":  cache_is_fresh(),
        "row_count":    len(DATA_CACHE["data"]),
    })


@app.route("/api/track", methods=["POST"])
@login_required
def track_usage():
    payload = request.json or {}
    u = session["user"]
    db.log_activity(
        u["email"],
        u["role"],
        payload.get("action", ""),
        payload.get("details", ""),
    )
    return jsonify({"status": "tracked"})


@app.route("/api/refresh", methods=["POST"])
@login_required
@superadmin_required
def force_refresh():
    u = session["user"]
    db.log_activity(u["email"], u["role"], "Force Refresh", "Superadmin triggered manual cache refresh")
    refresh_data(force=True)
    return jsonify({
        "status":       "refreshed",
        "last_updated": datetime.fromtimestamp(DATA_CACHE["timestamp"]).strftime("%d %b, %I:%M %p"),
        "next_refresh": next_cache_refresh().strftime("%d %b, %I:%M %p"),
        "row_count":    len(DATA_CACHE["data"]),
    })


# ══════════════════════════════════════════════════════════════
# 7. SUPERADMIN — USER MANAGEMENT
# ══════════════════════════════════════════════════════════════

@app.route("/admin")
@superadmin_required
def admin_panel():
    return render_template("admin.html", user=session["user"])


@app.route("/api/users", methods=["GET", "POST", "PUT", "DELETE"])
@superadmin_required
def manage_users():
    if request.method == "GET":
        return jsonify(db.get_all_users())

    if request.method in ("POST", "PUT"):
        data = request.json or {}
        email       = (data.get("email") or "").strip().lower()
        scope_type  = data.get("scope_type", "ALL")
        scope_value = data.get("scope_value")

        # Normalise SO list — accept comma string or Python list
        if scope_type == "SO":
            if isinstance(scope_value, str):
                scope_value = [x.strip() for x in scope_value.split(",") if x.strip()]
        else:
            scope_value = None

        try:
            db.upsert_user(
                email       = email,
                name        = data.get("name", ""),
                password    = data.get("password", ""),
                role        = data.get("role", "RH"),
                title       = data.get("title", ""),
                scope_type  = scope_type,
                scope_value = scope_value,
            )
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        return jsonify({"message": "User saved"})

    if request.method == "DELETE":
        email = (request.json or {}).get("email", "")
        if db.delete_user(email):
            return jsonify({"message": "User deleted"})
        return jsonify({"error": "User not found or cannot be deleted"}), 404


# ══════════════════════════════════════════════════════════════
# 8. SUPERADMIN — ANALYTICS & CACHE STATUS
# ══════════════════════════════════════════════════════════════

@app.route("/api/analytics")
@superadmin_required
def get_analytics():
    return jsonify(db.get_activity_log())


@app.route("/api/cache-status")
@superadmin_required
def cache_status():
    return jsonify({
        "is_fresh":     cache_is_fresh(),
        "loaded_at":    datetime.fromtimestamp(DATA_CACHE["timestamp"]).strftime("%d %b %Y, %I:%M:%S %p")
                        if DATA_CACHE["timestamp"] else "Never loaded",
        "window_start": get_cache_window_start().strftime("%d %b %Y, %I:%M %p"),
        "next_refresh": next_cache_refresh().strftime("%d %b %Y, %I:%M %p"),
        "row_count":    len(DATA_CACHE["data"]),
        "cache_hour":   Config.CACHE_HOUR,
    })


# ══════════════════════════════════════════════════════════════
# 9. STARTUP
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    db.init_db()    # create tables if they don't exist
    print("\n🚀 Heritage Samarth is running!")
    print(f"🔑 Secret key source: {'  .env file' if os.path.exists('.env') else '  environment variable'}")
    print(f"📅 Cache window: from {Config.CACHE_HOUR}:00 AM daily")
    print(f"⏰ Next refresh: {next_cache_refresh():%d %b %Y, %I:%M %p}\n")
    app.run(debug=False, host="0.0.0.0", port=5000)