from flask import Blueprint, render_template, request, session, jsonify,current_app 
from app.decorators import login_required
from app.services.cache_service import (
    refresh_data,
    cache_is_fresh,
    next_cache_refresh,
    format_loaded_at,
    get_cache,
)

dashboard_bp = Blueprint("dashboard", __name__)

# ── Power BI embed URLs (Publish to Web) ─────────────────────────────────────
POWERBI_REPORTS = {
    "Telangana":      "https://app.powerbi.com/view?r=eyJrIjoiYzNiNjRjNjMtZDA2MC00ZGUxLTlkMzctY2U1ZjkwY2VlNjNlIiwidCI6IjdmZjNjMWE5LTljYTAtNDBlNC1iMjdmLWRmZDU1M2M4OGZkZCJ9",
    "Andhra Pradesh": "https://app.powerbi.com/view?r=eyJrIjoiYjQ3MDA4MWUtZGQ5ZS00ODEzLTk1NTgtODAyZDQzNWVmOTA4IiwidCI6IjdmZjNjMWE5LTljYTAtNDBlNC1iMjdmLWRmZDU1M2M4OGZkZCJ9",
    "Karnataka":      "https://app.powerbi.com/view?r=eyJrIjoiZGNkZWY2OWUtYjljZi00YzMyLTg3ODAtZGJmYTM3ZDg2Y2VlIiwidCI6IjdmZjNjMWE5LTljYTAtNDBlNC1iMjdmLWRmZDU1M2M4OGZkZCJ9",
    "Tamil Nadu":     "https://app.powerbi.com/view?r=eyJrIjoiZDJiODVlMzktNGJhYy00ZTIxLTk2YWMtMjM0NmNjMDdjYzUxIiwidCI6IjdmZjNjMWE5LTljYTAtNDBlNC1iMjdmLWRmZDU1M2M4OGZkZCJ9",
    "Maharashtra":    "https://app.powerbi.com/view?r=eyJrIjoiZWM1MDUyM2UtNDQ0OS00OThjLTlmNDEtMDllMmMzZTYwMDg4IiwidCI6IjdmZjNjMWE5LTljYTAtNDBlNC1iMjdmLWRmZDU1M2M4OGZkZCJ9",
}

GLOBAL_REPORTS = {
    "HFL Schemes": "https://app.powerbi.com/view?r=eyJrIjoiZGQyY2QwMDctMzRhNi00ZDg0LWFlMjAtY2E3NzY4NzQxYzZiIiwidCI6IjdmZjNjMWE5LTljYTAtNDBlNC1iMjdmLWRmZDU1M2M4OGZkZCJ9",
    "ABCD Classification": "https://app.powerbi.com/view?r=eyJrIjoiY2M4M2VhM2MtYzY4OC00N2QzLWIyMzktNGFiMTVjMGMxM2JkIiwidCI6IjdmZjNjMWE5LTljYTAtNDBlNC1iMjdmLWRmZDU1M2M4OGZkZCJ9",
}

# Maps the short region codes in your DB → full names used in POWERBI_REPORTS
# Add more codes here if you see new ones in the data
REGION_CODE_MAP = {
    # Telangana variants
    "TG-1": "Telangana", "TG-2": "Telangana", "TG-3": "Telangana",
    "TG":   "Telangana",
    # Andhra Pradesh variants
    "AP-1": "Andhra Pradesh", "AP-2": "Andhra Pradesh", "AP-3": "Andhra Pradesh",
    "AP":   "Andhra Pradesh",
    # Karnataka variants
    "KA-1": "Karnataka", "KA-2": "Karnataka", "KA-3": "Karnataka",
    "KA":   "Karnataka", "KTK": "Karnataka",
    # Tamil Nadu variants
    "TN-1": "Tamil Nadu", "TN-2": "Tamil Nadu", "TN-3": "Tamil Nadu",
    "TN":   "Tamil Nadu",
    # Maharashtra variants
    "MH-1": "Maharashtra", "MH-2": "Maharashtra", "MH-3": "Maharashtra",
    "MH":   "Maharashtra",
}

WIDE_ACCESS_ROLES = {"Superadmin", "CXO"}


# ── Helper: resolve region from SO codes in the cache ────────────────────────
def _resolve_region_from_so(user: dict) -> str | None:
    cache = get_cache()
    if not cache or not cache.get("data"):
        return None

    col_map    = cache.get("column_map", {})
    so_idx     = col_map.get("SO")
    region_idx = col_map.get("Region")

    if so_idx is None or region_idx is None:
        return None

    scope_value = user.get("scope_value") or []
    allowed_sos = {str(v).replace(".0", "").strip() for v in scope_value}

    if not allowed_sos:
        return None

    for row in cache["data"]:
        so_val = str(row[so_idx]).replace(".0", "").strip()
        if so_val in allowed_sos:
            raw_region = str(row[region_idx]).strip()
            # Try exact match first (e.g. already "Tamil Nadu")
            if raw_region in POWERBI_REPORTS:
                return raw_region
            # Then try the code map (e.g. "TG-1" → "Telangana")
            mapped = REGION_CODE_MAP.get(raw_region)
            if mapped:
                return mapped
            # Last resort: case-insensitive prefix match
            raw_upper = raw_region.upper()
            for full_name in POWERBI_REPORTS:
                if raw_upper.startswith(full_name[:2].upper()):
                    return full_name

    return None


# ══════════════════════════════════════════════════════════════
# MAIN DASHBOARD
# ══════════════════════════════════════════════════════════════

@dashboard_bp.route("/")
@login_required
def index():
    return render_template("dashboard.html", user=session["user"])


# ══════════════════════════════════════════════════════════════
# POWER BI EMBED PAGE
# ══════════════════════════════════════════════════════════════

@dashboard_bp.route("/powerbi")
@login_required
def powerbi():
    current_user = session["user"]
    role         = current_user.get("role", "")

    if role in WIDE_ACCESS_ROLES:
        default_region = list(POWERBI_REPORTS.keys())[0]
        return render_template(
            "powerbi.html",
            user           = current_user,
            reports        = POWERBI_REPORTS,
            all_regions    = list(POWERBI_REPORTS.keys()),
            single_region  = None,
            default_region = default_region,
            embed_url      = None,
            global_reports = GLOBAL_REPORTS,
        )

    # RH / BM — warm cache then resolve region from SO codes
    refresh_data()
    region    = _resolve_region_from_so(current_user)
    embed_url = POWERBI_REPORTS.get(region) if region else None

    print(f"DEBUG powerbi route — resolved region: {repr(region)}, embed_url: {repr(embed_url)}")

    return render_template(
        "powerbi.html",
        user          = current_user,
        reports       = POWERBI_REPORTS,
        all_regions   = [],
        single_region = region or "Unknown",
        default_region= None,
        embed_url     = embed_url,
        global_reports = GLOBAL_REPORTS, 
    )


# ══════════════════════════════════════════════════════════════
# DATA API
# ══════════════════════════════════════════════════════════════

@dashboard_bp.route("/api/data")
@login_required
def api_data():
    refresh_data()

    cache        = get_cache()
    current_user = session["user"]
    columns      = list(cache["columns"])
    data         = list(cache["data"])
    col_map      = cache["column_map"]

    if current_user.get("scope_type") == "SO":
        if "SO" in col_map:
            scope_idx   = col_map["SO"]
            allowed_sos = {str(v).replace(".0", "").strip()
                           for v in (current_user.get("scope_value") or [])}
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

    return jsonify({
        "data":         data,
        "columns":      [{"title": c} for c in columns],
        "last_updated": format_loaded_at(),
        "next_refresh": next_cache_refresh().strftime("%d %b, %I:%M %p"),
        "cache_fresh":  cache_is_fresh(),
        "row_count":    len(cache["data"]),
    })


# ══════════════════════════════════════════════════════════════
# USAGE TRACKING
# ══════════════════════════════════════════════════════════════

@dashboard_bp.route("/api/track", methods=["POST"])
@login_required
def track_usage():
    payload = request.json or {}
    u       = session["user"]
    from app.models.database import log_activity
    log_activity(
        u["email"],
        u["role"],
        payload.get("action", ""),
        payload.get("details", ""),
    )
    return jsonify({"status": "tracked"})








# targets


# ══════════════════════════════════════════════════════════════
# TARGETS / BUDGET ACHIEVEMENT API
# Add this import at the top of your routes.py if not present:
#   from flask import current_app
#   import pyodbc
#   from datetime import date, datetime
# ══════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════
# TARGETS ROUTE  —  paste into routes.py (inside dashboard_bp)
#
# Prerequisites (already in your routes.py top-of-file imports):
#   from app.decorators import login_required
#   from flask import Blueprint, session, jsonify, current_app
#
# Add these imports at the top of routes.py if not present:
# ──────────────────────────────────────────────────────────────
import os
from app.services.mssql_service import get_mssql_connection, _clean_value
# ══════════════════════════════════════════════════════════════


def _get_targets_sql_path() -> str:
    """
    Resolves the path to sql/targets_achievement.sql.
 
    File layout:
        Heritage Samarth/          ← project root  (what we want)
            sql/
                targets_achievement.sql
            app/
                blueprints/
                    dashboard/
                        routes.py  ← __file__ is HERE  (4 levels deep)
                models/
                    database.py    ← that file uses 3 levels (only 3 deep)
 
    So we need dirname × 4, not × 3.
    Using current_app.root_path is the most robust approach:
        current_app.root_path  ==  .../Heritage Samarth/app
        one dirname up         ==  .../Heritage Samarth        ← project root
    """
    project_root = os.path.dirname(current_app.root_path)
    return os.path.join(project_root, "sql", "targets_achievement.sql")
 
 
def _fetch_targets_data() -> tuple[list[str], list[list]]:
    """
    Reads targets_achievement.sql and returns (columns, rows).
    Uses the same pattern as fetch_performance_data() in database.py.
    """
    sql_path = _get_targets_sql_path()
 
    if not os.path.exists(sql_path):
        raise FileNotFoundError(
            f"SQL file not found: {sql_path}\n"
            "Place targets_achievement.sql in the sql/ folder at project root."
        )
 
    with open(sql_path, encoding="utf-8") as fh:
        sql = fh.read()
 
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
        conn.close()
 
    return columns, rows
 
 
def _ci(columns: list[str], name: str) -> int:
    try:
        return columns.index(name)
    except ValueError:
        return -1
 
 
@dashboard_bp.route("/api/targets")
@login_required
def api_targets():
    try:
        columns, rows = _fetch_targets_data()
    except FileNotFoundError as exc:
        current_app.logger.error("targets SQL missing: %s", exc)
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        current_app.logger.error("api_targets DB error: %s", exc, exc_info=True)
        return jsonify({"error": "Database error — check server logs."}), 500
 
    current_user = session["user"]
    role         = current_user.get("role", "")
 
    if role not in WIDE_ACCESS_ROLES:
        scope_type  = current_user.get("scope_type",  "")
        scope_value = current_user.get("scope_value") or []
 
        if scope_type == "SO":
            so_i    = _ci(columns, "SalesOffice")
            allowed = {str(v).replace(".0", "").strip() for v in scope_value}
            if so_i != -1:
                rows = [r for r in rows
                        if str(r[so_i]).replace(".0", "").strip() in allowed]
 
        elif scope_type == "Region":
            reg_i   = _ci(columns, "Region")
            allowed = {str(v).strip() for v in scope_value}
            if reg_i != -1:
                rows = [r for r in rows
                        if str(r[reg_i]).strip() in allowed]
 
        elif scope_type not in ("ALL", None, ""):
            col_i     = _ci(columns, scope_type)
            scope_val = (str(scope_value[0]).strip()
                         if isinstance(scope_value, list) and scope_value
                         else str(scope_value).strip())
            if col_i != -1:
                rows = [r for r in rows
                        if str(r[col_i]).strip() == scope_val]
 
    di_col = _ci(columns, "DaysElapsed")
    dm_col = _ci(columns, "DaysInMonth")
    days_elapsed  = int(rows[0][di_col]) if rows and di_col != -1 else 1
    days_in_month = int(rows[0][dm_col]) if rows and dm_col != -1 else 30
 
    month_label = ""
    pm_col = _ci(columns, "PLANMONTH")
    if rows and pm_col != -1:
        from datetime import datetime as _dt
        try:
            month_label = _dt.strptime(str(rows[0][pm_col]), "%Y%m").strftime("%B %Y")
        except Exception:
            month_label = str(rows[0][pm_col])
 
    return jsonify({
        "columns":       [{"title": c} for c in columns],
        "data":          rows,
        "days_elapsed":  days_elapsed,
        "days_in_month": days_in_month,
        "month_label":   month_label,
    })