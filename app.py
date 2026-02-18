from flask import Flask, render_template, jsonify
import pyodbc
from decimal import Decimal
from datetime import date, datetime
import time

app = Flask(__name__)

# User Configuration
CURRENT_USER_ROLE = "CEO"  # Change to "Sales" to see SE_Mobile column
SLICER_COLUMNS = ['State', 'Region', 'SO_Name', 'CustomerGroup', 'SE_Name', 'Product', 'Sales_Trend']

# Cache Configuration (1 hour = instant loads for 50+ users)
CACHE = {}
CACHE_TTL = 3600  # seconds

def get_sql_data_cached():
    """Fetches data from SQL with intelligent caching for blazing performance."""
    global CACHE
    
    # Check cache first - instant return if data is fresh!
    if 'sales' in CACHE and (time.time() - CACHE['sales']['timestamp']) < CACHE_TTL:
        print("⚡ Fetching from cache (Lightning Fast!)...")
        return CACHE['sales']['columns'], CACHE['sales']['data']

    print("🔄 Executing SQL query (first load or cache expired)...")
    
    # Your database connection
    server = '10.0.1.71,4000'
    database = 'HeritageBI' 
    username = '127903'
    password = 'Raghavkumar.j@heritagefoods.in'
    driver = '{ODBC Driver 17 for SQL Server}' 
    conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    
    try:
        # Read SQL query from file
        with open('SQLQuery_performance_analysis.sql', 'r') as file:
            sql_query = file.read()

        # Execute query
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        
        # Get column names
        columns = [column[0] for column in cursor.description]
        raw_data = cursor.fetchall()
        
        # Clean and format data for JSON
        data = []
        for row in raw_data:
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
            data.append(clean_row)
            
        conn.close()

        # Cache the results for next hour
        CACHE['sales'] = {
            'timestamp': time.time(),
            'columns': columns,
            'data': data
        }
        
        print(f"✅ Loaded {len(data)} rows successfully and cached!")
        return columns, data

    except Exception as e:
        print(f"❌ Database error: {e}")
        return ["Error"], [[str(e)]]

@app.route('/')
def dashboard():
    """Main dashboard route - loads instantly"""
    return render_template(
        'dashboard.html',
        role=CURRENT_USER_ROLE,
        slicer_columns=SLICER_COLUMNS
    )

@app.route('/api/data')
def api_data():
    """API endpoint - applies role-based security and returns JSON"""
    # Get data (from cache or SQL)
    columns, data = get_sql_data_cached()
    
    # SECURITY: Strip PII based on user role
    role = CURRENT_USER_ROLE
    filtered_columns = list(columns)
    filtered_data = list(data)
    
    # Remove SE_Mobile column for CEO/COO (server-side security)
    if role != "Sales" and "SE_Mobile" in filtered_columns:
        pii_index = filtered_columns.index("SE_Mobile")
        filtered_columns.pop(pii_index)
        # Remove from every row
        filtered_data = [row[:pii_index] + row[pii_index+1:] for row in filtered_data]
        print(f"🔒 PII column removed for {role} role")

    # Convert to DataTables format
    dt_columns = [{"title": col} for col in filtered_columns]

    return jsonify({
        "data": filtered_data,
        "columns": dt_columns,
        "rowCount": len(filtered_data)
    })

@app.route('/api/clear-cache')
def clear_cache():
    """Manually clear cache if needed"""
    global CACHE
    CACHE = {}
    return jsonify({"message": "Cache cleared successfully"})

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🥛 Heritage Foods Sales Performance Dashboard")
    print("="*70)
    print(f"👤 User Role: {CURRENT_USER_ROLE}")
    print(f"🔐 PII Protection: {'Disabled (Sales View)' if CURRENT_USER_ROLE == 'Sales' else 'Enabled (Executive View)'}")
    print(f"⚡ Cache Duration: {CACHE_TTL} seconds ({CACHE_TTL//60} minutes)")
    print(f"📊 Filters: {', '.join(SLICER_COLUMNS)}")
    print("="*70)
    print("\n🚀 Starting server on http://localhost:5000")
    print("   Press Ctrl+C to stop\n")
    app.run(debug=True, host='0.0.0.0', port=5000)