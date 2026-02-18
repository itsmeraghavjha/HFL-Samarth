import os
import json
import time
import pyodbc
from decimal import Decimal
from datetime import date, datetime
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
    CACHE_TTL = 3600  # 1 Hour

DATA_CACHE = {
    "timestamp": 0,
    "columns": [],
    "data": [],
    "column_map": {}
}

# ==========================================
# 2. HELPER FUNCTIONS
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
    
    # Add new log at the top
    logs.insert(0, {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # Using 24hr format for easier JS parsing
        "email": email,
        "role": role,
        "action": action,
        "details": details
    })
    
    # Increased to 10,000 to support 30-day MAU calculations
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
    conn_str = f'DRIVER={driver};SERVER={Config.DB_SERVER};DATABASE={Config.DB_NAME};UID={Config.DB_USER};PWD={Config.DB_PASS}'
    return pyodbc.connect(conn_str)

def refresh_data():
    global DATA_CACHE
    if (time.time() - DATA_CACHE['timestamp']) < Config.CACHE_TTL and DATA_CACHE['data']:
        return

    try:
        with open('SQLQuery_performance_analysis.sql', 'r') as f: sql_query = f.read()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql_query)
        
        columns = [column[0] for column in cursor.description]
        formatted_data = []
        for row in cursor.fetchall():
            clean_row = []
            for val in row:
                if val is None: clean_row.append("")
                elif isinstance(val, Decimal): clean_row.append(float(val))
                elif isinstance(val, (date, datetime)): clean_row.append(val.strftime("%Y-%m-%d"))
                else: clean_row.append(val)
            formatted_data.append(clean_row)
        conn.close()
        
        DATA_CACHE.update({
            "timestamp": time.time(),
            "columns": columns,
            "data": formatted_data,
            "column_map": {name: i for i, name in enumerate(columns)}
        })
    except Exception as e: print(f"❌ DB Error: {e}")

# ==========================================
# 3. AUTH & MAIN ROUTES
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
# 4. API & DATA ENDPOINTS
# ==========================================
@app.route('/api/data')
@login_required
def api_data():
    refresh_data()
    current_user = session['user']
    columns = list(DATA_CACHE['columns'])
    data = list(DATA_CACHE['data'])
    col_map = DATA_CACHE['column_map']
    
    if current_user.get('scope_type') == 'SO':
        if 'SO' in col_map:
            scope_idx = col_map['SO']
            allowed_sos = set(current_user['scope_value'])
            data = [row for row in data if row[scope_idx] is not None and str(row[scope_idx]).replace('.0', '').strip() in allowed_sos]
            
    elif current_user.get('scope_type') not in ['ALL', None, '']:
        scope_col = current_user['scope_type']
        scope_val = current_user['scope_value']
        if scope_col in col_map:
            scope_idx = col_map[scope_col]
            data = [row for row in data if str(row[scope_idx]).strip() == str(scope_val).strip()]
    
    return jsonify({
        "data": data,
        "columns": [{"title": c} for c in columns],
        "last_updated": datetime.fromtimestamp(DATA_CACHE['timestamp']).strftime('%I:%M %p') if DATA_CACHE['timestamp'] else "Never"
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

# ==========================================
# 5. SUPERADMIN ROUTES
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
            "password": data.get('password'), "name": data.get('name'), "role": data.get('role'),
            "title": data.get('title'), "scope_type": data.get('scope_type'), "scope_value": scope_val
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

if __name__ == '__main__':
    print("\n🚀 Heritage Samarth System is Running!")
    app.run(debug=True, host='0.0.0.0', port=5000)