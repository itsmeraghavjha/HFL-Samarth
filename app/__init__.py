import os
from flask import Flask
from app.config import config_map


def create_app(config_name: str = None) -> Flask:
    """
    Application factory.

    Creates and configures a Flask app instance.
    Called by wsgi.py (production) and run.py (development).

    Args:
        config_name: one of 'development', 'production', 'testing'
                     defaults to FLASK_ENV environment variable,
                     falls back to 'development' if not set.
    """

    # ── Resolve config name ───────────────────────────────────
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    # ── Create app ────────────────────────────────────────────
    app = Flask(
        __name__,
        template_folder = "../templates",   # templates/ at project root
        static_folder   = "../static",      # static/ at project root
    )

    # ── Load config ───────────────────────────────────────────
    app.config.from_object(config_map[config_name])

    # ── Register blueprints ───────────────────────────────────
    _register_blueprints(app)

    # ── Register error handlers ───────────────────────────────
    _register_error_handlers(app)

    # ── Start background cache scheduler ──────────────────────
    # Runs as a daemon thread — triggers a DB refresh daily at CACHE_HOUR
    # so data is ready before the first user request of the day.
    #
    # WHY THE os.environ CHECK:
    # Flask debug mode uses Werkzeug's reloader which spawns TWO processes:
    #   Process 1 (reloader) — watches files for changes, WERKZEUG_RUN_MAIN not set
    #   Process 2 (worker)   — actually handles HTTP requests, WERKZEUG_RUN_MAIN = 'true'
    # Without this check, the scheduler starts in Process 1, fills ITS cache,
    # but all requests go to Process 2 which has a completely separate empty cache.
    # The check ensures the scheduler only starts in the process that serves requests.
    import os
    if config_name != "testing":
        in_worker = (not app.debug) or (os.environ.get("WERKZEUG_RUN_MAIN") == "true")
        if in_worker:
            from app.services.scheduler import start_cache_scheduler
            start_cache_scheduler(app)

    # ── Startup log ───────────────────────────────────────────
    app.logger.info(
        f"Heritage Samarth started — "
        f"env={config_name}, "
        f"cache_hour={app.config['CACHE_HOUR']}:00 AM"
    )

    return app


# ══════════════════════════════════════════════════════════════
# BLUEPRINTS
# ══════════════════════════════════════════════════════════════

def _register_blueprints(app: Flask) -> None:
    from app.blueprints.auth.routes      import auth_bp
    from app.blueprints.dashboard.routes import dashboard_bp
    from app.blueprints.admin.routes     import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)


# ══════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ══════════════════════════════════════════════════════════════

def _register_error_handlers(app: Flask) -> None:

    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template("errors/500.html"), 500