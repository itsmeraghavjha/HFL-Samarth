import os
import json
import time
import pyodbc
from decimal import Decimal
from datetime import date, datetime, timedelta
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from functools import wraps

app = Flask(__name__, static_folder='static')

# ==========================================
# 1. SECURITY & CONFIGURATION
# ==========================================
app.secret_key = os.environ.get('SECRET_KEY', 'Heritage_Samarth_Secure_Key_2024')
USERS_FILE = 'users.json'
ANALYTICS_FILE = 'analytics.json'

class Config:
    DB_SERVER = '10.0.1.71,4000'
    DB_NAME = 'HeritageBI'
    DB_USER = '127903'
    DB_PASS = 'Raghavkumar.j@heritagefoods.in'

    # ─────────────────────────────────────────────────────────────
    # CACHE STRATEGY: Daily 9 AM Window
    #
    # The database refreshes overnight (typically 2–5 AM).
    # We want to load fresh data ONCE at/after 9 AM each morning,
    # then serve that same snapshot to all users for the full day.
    #
    # Rule: The cache is considered VALID if it was populated
    # after today's 9:00:00 AM. Before 9 AM, the previous day's
    # cache (loaded after yesterday's 9 AM) is still valid.
    #
    # This means:
    #   - First request at or after 9 AM → triggers a DB fetch
    #   - All subsequent requests that day → served from cache
    #   - No TTL countdown — cache is date-window based, not time-delta based
    # ─────────────────────────────────────────────────────────────
    CACHE_HOUR = 9   # 9 AM — change this if your DB refresh time shifts


DATA_CACHE = {
    "timestamp": 0,       # epoch float of when cache was last populated
    "columns": [],
    "data": [],
    "column_map": {}
}


# ==========================================
# 2. CACHE WINDOW LOGIC
# ==========================================

def get_cache_window_start():
    """
    Returns the datetime of the most recent 9 AM cutoff.

    Logic:
      - If current time is 9:00 AM or later today  → return today @ 9:00:00
      - If current time is before 9:00 AM today    → return yesterday @ 9:00:00

    This means the "valid window" is always:
        [most_recent_9am, next_9am)

    Example timeline:
        08:55 AM today  → window start = yesterday 9:00 AM
        09:01 AM today  → window start = today 9:00 AM
        11:59 PM today  → window start = today 9:00 AM
    """
    now = datetime.now()
    today_9am = now.replace(hour=Config.CACHE_HOUR, minute=0, second=0, microsecond=0)

    if now >= today_9am:
        return today_9am
    else:
        return today_9am - timedelta(days=1)


def cache_is_fresh():
    """
    Returns True if the cache was populated within the current 9 AM window.
    Returns False if:
      - Cache is empty (first ever run)
      - Cache was loaded before today's 9 AM (i.e., it's stale from yesterday or older)
    """
    if not DATA_CACHE['data'] or DATA_CACHE['timestamp'] == 0:
        return False

    cache_loaded_at = datetime.fromtimestamp(DATA_CACHE['timestamp'])
    window_start = get_cache_window_start()

    return cache_loaded_at >= window_start


def next_cache_refresh():
    """
    Returns the datetime of the next scheduled cache refresh (next 9 AM).
    Used for display in the UI header.
    """
    now = datetime.now()
    today_9am = now.replace(hour=Config.CACHE_HOUR, minute=0, second=0, microsecond=0)

    if now < today_9am:
        return today_9am                       # today's 9 AM hasn't happened yet
    else:
        return today_9am + timedelta(days=1)   # tomorrow's 9 AM


# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================

def load_users():
    if not os.path.exists(USERS_FILE): return {}
    with open(USERS_FILE, 'r') as f: return json.load(f)

def save_users(users_dict):
    with open(USERS_FILE, 'w') as f: json.dump(users_dict, f, indent=4)

def log_activity(email, role, action, details):
    """Logs user activity to a local JSON file for the Admin Dashboard."""
    logs = []
    if os.path.exists(ANALYTICS_FILE):
        try:
            with open(ANALYTICS_FILE, 'r') as f: logs = json.load(f)
        except: pass

    logs.insert(0, {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "email": email,
        "role": role,
        "action": action,
        "details": details
    })

    with open(ANALYTICS_FILE, 'w') as f:
        json.dump(logs[:10000], f, indent=4)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session: return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session['user'].get('role') != 'Superadmin':
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def get_db_connection():
    driver = '{ODBC Driver 17 for SQL Server}'
    conn_str = (
        f'DRIVER={driver};SERVER={Config.DB_SERVER};'
        f'DATABASE={Config.DB_NAME};UID={Config.DB_USER};PWD={Config.DB_PASS}'
    )
    return pyodbc.connect(conn_str)


def refresh_data(force=False):
    """
    Loads data from DB into DATA_CACHE.

    Normal call:  refresh_data()
      → Only fetches if cache is stale (outside current 9 AM window)

    Force call:   refresh_data(force=True)
      → Always fetches, regardless of cache state.
      → Used by the /api/refresh endpoint (Superadmin only).
    """
    global DATA_CACHE

    # Skip fetch if cache is still fresh — UNLESS force=True
    if not force and cache_is_fresh():
        return

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Fetching fresh data from DB...")

    try:
        with open('SQLQuery_performance_analysis.sql', 'r') as f:
            sql_query = f.read()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql_query)

        columns = [column[0] for column in cursor.description]
        formatted_data = []

        for row in cursor.fetchall():
            clean_row = []
            for val in row:
                if val is None:
                    clean_row.append("")
                elif isinstance(val, Decimal):
                    clean_row.append(float(val))
                elif isinstance(val, (date, datetime)):
                    clean_row.append(val.strftime("%Y-%m-%d"))
                else:
                    clean_row.append(val)
            formatted_data.append(clean_row)

        conn.close()

        DATA_CACHE.update({
            "timestamp": time.time(),
            "columns": columns,
            "data": formatted_data,
            "column_map": {name: i for i, name in enumerate(columns)}
        })

        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Cache populated — {len(formatted_data):,} rows. Valid until {next_cache_refresh().strftime('%d %b %Y, %I:%M %p')}.")

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ DB Error: {e}")


# ==========================================
# 4. AUTH & MAIN ROUTES
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        users = load_users()
        user = users.get(email)

        if user and user['password'] == password:
            user['email'] = email
            session['user'] = user
            log_activity(email, user['role'], "Login", "User authenticated")

            if user['role'] == 'Superadmin': return redirect(url_for('admin_panel'))
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid credentials. Please try again.'

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    if 'user' in session:
        log_activity(session['user']['email'], session['user']['role'], "Logout", "User signed out manually")
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html', user=session['user'])


# ==========================================
# 5. API & DATA ENDPOINTS
# ==========================================

@app.route('/api/data')
@login_required
def api_data():
    refresh_data()   # No-op if cache is fresh; fetches if stale

    current_user = session['user']
    columns = list(DATA_CACHE['columns'])
    data = list(DATA_CACHE['data'])
    col_map = DATA_CACHE['column_map']

    # Row-Level Security filtering
    if current_user.get('scope_type') == 'SO':
        if 'SO' in col_map:
            scope_idx = col_map['SO']
            allowed_sos = set(current_user['scope_value'])
            data = [
                row for row in data
                if row[scope_idx] is not None
                and str(row[scope_idx]).replace('.0', '').strip() in allowed_sos
            ]

    elif current_user.get('scope_type') not in ['ALL', None, '']:
        scope_col = current_user['scope_type']
        scope_val = current_user['scope_value']
        if scope_col in col_map:
            scope_idx = col_map[scope_col]
            data = [
                row for row in data
                if str(row[scope_idx]).strip() == str(scope_val).strip()
            ]

    # Build cache metadata for UI display
    cache_loaded_at = (
        datetime.fromtimestamp(DATA_CACHE['timestamp']).strftime('%d %b, %I:%M %p')
        if DATA_CACHE['timestamp'] else "Never"
    )
    next_refresh = next_cache_refresh().strftime('%d %b, %I:%M %p')

    return jsonify({
        "data": data,
        "columns": [{"title": c} for c in columns],
        "last_updated": cache_loaded_at,
        "next_refresh": next_refresh,             # NEW — shown in dashboard header
        "cache_fresh": cache_is_fresh(),          # NEW — used for stale-data banner logic
        "row_count": len(DATA_CACHE['data'])      # NEW — total rows before RLS filter
    })


@app.route('/api/track', methods=['POST'])
@login_required
def track_usage():
    data = request.json
    log_activity(
        session['user']['email'],
        session['user']['role'],
        data.get('action'),
        data.get('details')
    )
    return jsonify({"status": "tracked"})


@app.route('/api/refresh', methods=['POST'])
@login_required
@superadmin_required
def force_refresh():
    """
    Superadmin-only endpoint to force a DB re-fetch outside the 9 AM schedule.
    Useful after an emergency DB reload or data correction.
    Logs the action for audit trail.
    """
    log_activity(
        session['user']['email'],
        session['user']['role'],
        "Force Refresh",
        f"Superadmin triggered manual cache refresh"
    )

    refresh_data(force=True)

    return jsonify({
        "status": "refreshed",
        "last_updated": datetime.fromtimestamp(DATA_CACHE['timestamp']).strftime('%d %b, %I:%M %p'),
        "next_refresh": next_cache_refresh().strftime('%d %b, %I:%M %p'),
        "row_count": len(DATA_CACHE['data'])
    })


# ==========================================
# 6. SUPERADMIN ROUTES
# ==========================================

@app.route('/admin')
@superadmin_required
def admin_panel():
    return render_template('admin.html', user=session['user'])

@app.route('/api/users', methods=['GET', 'POST', 'PUT', 'DELETE'])
@superadmin_required
def manage_users():
    users = load_users()
    if request.method == 'GET': return jsonify(users)

    if request.method in ['POST', 'PUT']:
        data = request.json
        email = data.get('email')
        scope_val = data.get('scope_value')
        if data.get('scope_type') == 'SO' and isinstance(scope_val, str):
            scope_val = [x.strip() for x in scope_val.split(',') if x.strip()]

        users[email] = {
            "password": data.get('password'),
            "name": data.get('name'),
            "role": data.get('role'),
            "title": data.get('title'),
            "scope_type": data.get('scope_type'),
            "scope_value": scope_val
        }
        save_users(users)
        return jsonify({"message": "User saved"})

    if request.method == 'DELETE':
        email = request.json.get('email')
        if email in users:
            del users[email]
            save_users(users)
            return jsonify({"message": "User deleted"})
        return jsonify({"error": "User not found"}), 404

@app.route('/api/analytics')
@superadmin_required
def get_analytics():
    if not os.path.exists(ANALYTICS_FILE): return jsonify([])
    try:
        with open(ANALYTICS_FILE, 'r') as f: return jsonify(json.load(f))
    except:
        return jsonify([])

@app.route('/api/cache-status')
@superadmin_required
def cache_status():
    """
    Returns current cache state for the admin panel to display.
    """
    return jsonify({
        "is_fresh": cache_is_fresh(),
        "loaded_at": datetime.fromtimestamp(DATA_CACHE['timestamp']).strftime('%d %b %Y, %I:%M:%S %p') if DATA_CACHE['timestamp'] else "Never loaded",
        "window_start": get_cache_window_start().strftime('%d %b %Y, %I:%M %p'),
        "next_refresh": next_cache_refresh().strftime('%d %b %Y, %I:%M %p'),
        "row_count": len(DATA_CACHE['data']),
        "cache_hour": Config.CACHE_HOUR
    })


if __name__ == '__main__':
    print("\n🚀 Heritage Samarth System is Running!")
    print(f"📅 Cache strategy: Daily window from {Config.CACHE_HOUR}:00 AM")
    print(f"⏰ Next cache load: {next_cache_refresh().strftime('%d %b %Y, %I:%M %p')}\n")
    app.run(debug=True, host='0.0.0.0', port=5000)