from flask import Blueprint, render_template, request, session, jsonify
from app.decorators import login_required
from app.services.cache_service import (
    refresh_data,
    cache_is_fresh,
    next_cache_refresh,
    format_loaded_at,
)

dashboard_bp = Blueprint("dashboard", __name__)


# ══════════════════════════════════════════════════════════════
# MAIN DASHBOARD
# ══════════════════════════════════════════════════════════════

@dashboard_bp.route("/")
@login_required
def index():
    return render_template("dashboard.html", user=session["user"])


# ══════════════════════════════════════════════════════════════
# DATA API
# ══════════════════════════════════════════════════════════════

@dashboard_bp.route("/api/data")
@login_required
def api_data():
    refresh_data()   # no-op if cache is fresh

    from app.services.cache_service import get_cache
    cache       = get_cache()
    current_user = session["user"]
    columns     = list(cache["columns"])
    data        = list(cache["data"])
    col_map     = cache["column_map"]

    # ── Row-Level Security ────────────────────────────────────
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