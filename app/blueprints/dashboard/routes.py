from flask import Blueprint, render_template, request, session, jsonify
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