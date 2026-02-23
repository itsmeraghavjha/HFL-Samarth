from flask import Blueprint, render_template, request, session, jsonify
from app.decorators import login_required, superadmin_required
from app.models.database import (
    log_activity,
    get_all_users,
    upsert_user,
    delete_user,
    get_activity_log,
)
from app.services.cache_service import (
    refresh_data,
    get_cache,
    get_cache_status,
    next_cache_refresh,
    format_loaded_at,
)
from datetime import datetime

admin_bp = Blueprint("admin", __name__)


# ══════════════════════════════════════════════════════════════
# ADMIN PANEL
# ══════════════════════════════════════════════════════════════

@admin_bp.route("/admin")
@login_required
@superadmin_required
def panel():
    return render_template("admin.html", user=session["user"])


# ══════════════════════════════════════════════════════════════
# USER MANAGEMENT
# ══════════════════════════════════════════════════════════════

@admin_bp.route("/api/users", methods=["GET", "POST", "PUT", "DELETE"])
@login_required
@superadmin_required
def manage_users():
    if request.method == "GET":
        return jsonify(get_all_users())

    if request.method in ("POST", "PUT"):
        data        = request.json or {}
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
            upsert_user(
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
        if delete_user(email):
            return jsonify({"message": "User deleted"})
        return jsonify({"error": "User not found or cannot be deleted"}), 404


# ══════════════════════════════════════════════════════════════
# ANALYTICS & CACHE
# ══════════════════════════════════════════════════════════════

@admin_bp.route("/api/analytics")
@login_required
@superadmin_required
def get_analytics():
    return jsonify(get_activity_log())


@admin_bp.route("/api/cache-status")
@login_required
@superadmin_required
def cache_status():
    return jsonify(get_cache_status())


@admin_bp.route("/api/refresh", methods=["POST"])
@login_required
@superadmin_required
def force_refresh():
    u = session["user"]
    log_activity(
        u["email"],
        u["role"],
        "Force Refresh",
        "Superadmin triggered manual cache refresh",
    )

    error = refresh_data(force=True)
    if error:
        return jsonify({"status": "error", "message": error}), 500

    cache = get_cache()
    return jsonify({
        "status":       "refreshed",
        "last_updated": format_loaded_at(),
        "next_refresh": next_cache_refresh().strftime("%d %b, %I:%M %p"),
        "row_count":    len(cache["data"]),
    })