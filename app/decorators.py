from functools import wraps
from flask import session, redirect, url_for, abort


def login_required(f):
    """
    Redirects unauthenticated users to the login page.

    Usage:
        @login_required
        def my_route():
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def superadmin_required(f):
    """
    Returns 403 if the logged-in user is not a Superadmin.
    Always stack BELOW @login_required so unauthenticated users
    get redirected to login rather than seeing a 403.

    Usage:
        @login_required
        @superadmin_required
        def my_route():
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session or session["user"].get("role") != "Superadmin":
            abort(403)
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    """
    Generic role gate — pass one or more allowed role strings.
    Returns 403 if the user's role is not in the allowed list.
    Always stack BELOW @login_required.

    Usage:
        @login_required
        @role_required("Superadmin", "CXO")
        def my_route():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user" not in session:
                abort(403)
            if session["user"].get("role") not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator