import os
import pyodbc
from decimal import Decimal
from datetime import date, datetime
from flask import current_app


def get_mssql_connection():
    """
    Opens and returns a raw pyodbc connection using config values.
    Caller is responsible for closing it.
    """
    driver = "{ODBC Driver 17 for SQL Server}"
    conn_str = (
        f"DRIVER={driver};"
        f"SERVER={current_app.config['MSSQL_SERVER']};"
        f"DATABASE={current_app.config['MSSQL_DB']};"
        f"UID={current_app.config['MSSQL_USER']};"
        f"PWD={current_app.config['MSSQL_PASS']}"
    )
    return pyodbc.connect(conn_str)


def _get_sql_path() -> str:
    """
    Returns the absolute path to the SQL file.
    Works regardless of where the app is launched from.
    """
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    return os.path.join(project_root, "sql", "performance_analysis.sql")


def _clean_value(val):
    """
    Converts a raw DB value into a JSON-safe Python type.
    - None        → ""
    - Decimal     → float
    - date/datetime → "YYYY-MM-DD" string
    - everything else → as-is
    """
    if val is None:
        return ""
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, (date, datetime)):
        return val.strftime("%Y-%m-%d")
    return val


def fetch_performance_data() -> tuple[list[str], list[list]]:
    """
    Reads the SQL file, runs it against MSSQL, and returns:
        columns  — list of column name strings
        rows     — list of cleaned rows (each row is a list)

    Raises an exception on any DB or file error — caller handles it.
    """
    sql_path = _get_sql_path()

    if not os.path.exists(sql_path):
        raise FileNotFoundError(
            f"SQL file not found at: {sql_path}\n"
            f"Make sure you moved SQLQuery_performance_analysis.sql "
            f"to the sql/ folder and renamed it to performance_analysis.sql"
        )

    with open(sql_path, encoding="utf-8") as f:
        sql = f.read()

    conn   = get_mssql_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(sql)
        columns = [col[0] for col in cursor.description]
        rows    = [
            [_clean_value(val) for val in row]
            for row in cursor.fetchall()
        ]
    finally:
        conn.close()   # always close, even if fetchall() raises

    return columns, rows