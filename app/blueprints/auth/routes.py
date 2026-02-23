from flask import Blueprint, render_template, request, session, redirect, url_for
auth_bp = Blueprint("auth", __name__)
from app.decorators import login_required
from app.models.database import (
    get_user_by_email,
    verify_password,
    record_login_attempt,
    is_locked_out,
    touch_last_login,
    log_activity,
    can_request_reset,
    create_reset_token,
    validate_reset_token,
    consume_reset_token,
    prune_expired_tokens,
    LOCKOUT_WINDOW_MINUTES,
)
from app.services.email_service import send_reset_email


# ══════════════════════════════════════════════════════════════
# LOGIN / LOGOUT
# ══════════════════════════════════════════════════════════════

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Already logged in — send to dashboard
    if "user" in session:
        return redirect(url_for("dashboard.index"))

    error = None

    if request.method == "POST":
        email    = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        ip       = request.remote_addr

        # ── Rate limit check ─────────────────────────────────
        if is_locked_out(email):
            error = (
                f"Too many failed attempts. "
                f"Please wait {LOCKOUT_WINDOW_MINUTES} minutes before trying again."
            )
            return render_template("login.html", error=error)

        # ── Credential check ─────────────────────────────────
        user = get_user_by_email(email)

        if user and verify_password(password, user["password_hash"]):
            record_login_attempt(email, ip, success=True)
            touch_last_login(email)

            # Store only safe fields — never store the password hash
            session.permanent = True
            session["user"] = {
                "email":       email,
                "name":        user["name"],
                "role":        user["role"],
                "title":       user["title"],
                "scope_type":  user["scope_type"],
                "scope_value": user["scope_value"],
            }

            log_activity(email, user["role"], "Login", "User authenticated")

            if user["role"] == "Superadmin":
                return redirect(url_for("admin.panel"))
            return redirect(url_for("dashboard.index"))

        # Deliberately vague — don't reveal whether email exists
        record_login_attempt(email, ip, success=False)
        error = "Invalid credentials. Please try again."

    return render_template("login.html", error=error)


@auth_bp.route("/logout")
def logout():
    if "user" in session:
        u = session["user"]
        log_activity(u["email"], u["role"], "Logout", "User signed out manually")
    session.clear()
    return redirect(url_for("auth.login"))


# ══════════════════════════════════════════════════════════════
# FORGOT PASSWORD
# ══════════════════════════════════════════════════════════════

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if "user" in session:
        return redirect(url_for("dashboard.index"))

    message = None
    error   = None

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()

        if not email:
            error = "Please enter your email address."
        else:
            user = get_user_by_email(email)

            if user and can_request_reset(email):
                token   = create_reset_token(email)
                ok, err = send_reset_email(email, token)

                if not ok:
                    # Log SMTP failure server-side but never expose to user
                    from flask import current_app
                    current_app.logger.error(f"Reset email failed for {email}: {err}")

            # Always show the same message — prevents account enumeration
            message = (
                "If that email is registered, you'll receive a reset link shortly. "
                "Check your inbox and spam folder."
            )

    return render_template("forgot_password.html", message=message, error=error)


# ══════════════════════════════════════════════════════════════
# RESET PASSWORD
# ══════════════════════════════════════════════════════════════

@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if "user" in session:
        return redirect(url_for("dashboard.index"))

    token = request.args.get("token") or request.form.get("token") or ""
    error = None

    # ── GET: pre-validate token so expired links show error immediately ──
    if request.method == "GET":
        token_valid = bool(token and validate_reset_token(token))
        return render_template(
            "reset_password.html",
            token        = token,
            token_invalid = not token_valid,
            error        = None,
        )

    # ── POST: apply new password ──────────────────────────────
    password  = request.form.get("password", "")
    password2 = request.form.get("password2", "")

    if not password or len(password) < 8:
        error = "Password must be at least 8 characters."
    elif password != password2:
        error = "Passwords do not match."
    else:
        email = validate_reset_token(token)
        if not email:
            return render_template(
                "reset_password.html",
                token         = token,
                token_invalid = True,
                error         = None,
            )

        success = consume_reset_token(token, password)
        if success:
            log_activity(email, "", "Password Reset", "User reset password via email link")
            prune_expired_tokens()
            return render_template(
                "reset_password.html",
                token         = "",
                token_invalid = False,
                success       = True,
                error         = None,
            )
        else:
            error = "This reset link has already been used or expired. Please request a new one."

    return render_template(
        "reset_password.html",
        token         = token,
        token_invalid = False,
        error         = error,
    )