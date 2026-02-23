import time
from datetime import datetime, timedelta
from typing import Optional

from flask import current_app


# ── In-memory cache store ─────────────────────────────────────────────────────
# This lives for the lifetime of the Python process.
# All requests share this same dict.
_DATA_CACHE: dict = {
    "timestamp":  0,       # epoch float — when cache was last populated
    "columns":    [],      # list of column name strings
    "data":       [],      # list of rows (each row is a list)
    "column_map": {},      # column name → index, for fast RLS lookups
}


# ── Public accessors ──────────────────────────────────────────────────────────

def get_cache() -> dict:
    """Returns the raw cache dict. Read-only — don't mutate directly."""
    return _DATA_CACHE


def cache_is_fresh() -> bool:
    """
    Returns True if the cache was populated within the current 9 AM window.

    Logic:
      - If current time >= 9 AM today → window opened today at 9 AM
      - If current time <  9 AM today → window opened yesterday at 9 AM
      - Cache is fresh if it was loaded AFTER the window start
    """
    if not _DATA_CACHE["data"] or _DATA_CACHE["timestamp"] == 0:
        return False

    loaded_at    = datetime.fromtimestamp(_DATA_CACHE["timestamp"])
    window_start = _get_cache_window_start()
    return loaded_at >= window_start


def next_cache_refresh() -> datetime:
    """
    Returns the datetime of the next scheduled 9 AM refresh.
    Used by the UI to show 'Next refresh at ...'
    """
    cache_hour = current_app.config["CACHE_HOUR"]
    now        = datetime.now()
    today_9am  = now.replace(hour=cache_hour, minute=0, second=0, microsecond=0)
    return today_9am if now < today_9am else today_9am + timedelta(days=1)


def get_cache_window_start() -> datetime:
    """Public wrapper — used by admin cache status endpoint."""
    return _get_cache_window_start()


def refresh_data(force: bool = False) -> Optional[str]:
    """
    Loads fresh data from MSSQL into the cache.

    Normal call:  refresh_data()
      → Skips fetch if cache is still fresh.

    Force call:   refresh_data(force=True)
      → Always fetches, ignores cache state.
      → Used by the Superadmin 'Force Refresh' button.

    Returns:
      None         on success
      str          error message on failure
    """
    if not force and cache_is_fresh():
        return None

    current_app.logger.info("Fetching fresh data from MSSQL...")

    try:
        # Import here to avoid circular imports at module load time
        from app.services.mssql_service import fetch_performance_data

        columns, rows = fetch_performance_data()

        _DATA_CACHE.update({
            "timestamp":  time.time(),
            "columns":    columns,
            "data":       rows,
            "column_map": {name: i for i, name in enumerate(columns)},
        })

        current_app.logger.info(
            f"Cache ready — {len(rows):,} rows. "
            f"Next refresh: {next_cache_refresh():%d %b %Y, %I:%M %p}"
        )
        return None

    except Exception as e:
        current_app.logger.error(f"Cache refresh failed: {e}")
        return str(e)


def get_cache_status() -> dict:
    """
    Returns a dict describing current cache state.
    Used by the /api/cache-status endpoint.
    """
    return {
        "is_fresh":     cache_is_fresh(),
        "loaded_at":    (
            datetime.fromtimestamp(_DATA_CACHE["timestamp"]).strftime("%d %b %Y, %I:%M:%S %p")
            if _DATA_CACHE["timestamp"] else "Never loaded"
        ),
        "window_start": _get_cache_window_start().strftime("%d %b %Y, %I:%M %p"),
        "next_refresh": next_cache_refresh().strftime("%d %b %Y, %I:%M %p"),
        "row_count":    len(_DATA_CACHE["data"]),
        "cache_hour":   current_app.config["CACHE_HOUR"],
    }


def format_loaded_at() -> str:
    """Returns a short human-readable string of when data was last loaded."""
    if not _DATA_CACHE["timestamp"]:
        return "Never"
    return datetime.fromtimestamp(_DATA_CACHE["timestamp"]).strftime("%d %b, %I:%M %p")


# ── Private helpers ───────────────────────────────────────────────────────────

def _get_cache_window_start() -> datetime:
    """
    Returns the start of the current 9 AM cache window.
    Private — internal use only.
    """
    cache_hour = current_app.config["CACHE_HOUR"]
    now        = datetime.now()
    today_9am  = now.replace(hour=cache_hour, minute=0, second=0, microsecond=0)
    return today_9am if now >= today_9am else today_9am - timedelta(days=1)