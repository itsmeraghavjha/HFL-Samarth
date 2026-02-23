from dotenv import load_dotenv
load_dotenv() 

import os
from datetime import timedelta


class BaseConfig:
    """
    Settings shared across ALL environments.
    Never put secrets here — use .env for that.
    """

    # ── Flask ────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY is not set. "
            "Run: python -c \"import secrets; print(secrets.token_hex(32))\" "
            "and add it to your .env file."
        )

    # ── Session ──────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY  = True
    SESSION_COOKIE_SAMESITE  = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)

    # ── MSSQL ────────────────────────────────────────────────
    MSSQL_SERVER = os.environ.get("MSSQL_SERVER", "10.0.1.71,4000")
    MSSQL_DB     = os.environ.get("MSSQL_DB",     "HeritageBI")
    MSSQL_USER   = os.environ.get("MSSQL_USER",   "")
    MSSQL_PASS   = os.environ.get("MSSQL_PASS",   "")

    # ── Cache ────────────────────────────────────────────────
    # Hour of day (24h) when the daily cache window opens.
    # First request at or after this hour triggers a DB fetch.
    CACHE_HOUR = int(os.environ.get("CACHE_HOUR", "9"))

    # ── SMTP ─────────────────────────────────────────────────
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASS = os.environ.get("SMTP_PASS", "")
    SMTP_FROM = os.environ.get(
        "SMTP_FROM", "Samarth Analytics <noreply@heritagefoods.in>"
    )

    # ── App ──────────────────────────────────────────────────
    APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:5000")


class DevelopmentConfig(BaseConfig):
    """
    Local development.
    Debug mode on, cookies don't require HTTPS.
    """
    DEBUG                = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(BaseConfig):
    """
    Live server.
    Debug OFF, cookies only sent over HTTPS.
    """
    DEBUG                = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(BaseConfig):
    """
    Automated tests.
    Uses a fixed secret key so tests are deterministic.
    """
    TESTING              = True
    DEBUG                = True
    SESSION_COOKIE_SECURE = False
    SECRET_KEY           = "test-only-secret-key-do-not-use-in-prod"


# ── Registry ─────────────────────────────────────────────────────────────────
# Import the right config by name:
#   app.config.from_object(config_map["development"])
config_map = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
}