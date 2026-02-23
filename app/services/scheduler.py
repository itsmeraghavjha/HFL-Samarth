"""
app/services/scheduler.py — Heritage Samarth | Background Cache Scheduler
==========================================================================
Starts a daemon thread that wakes every 60 seconds and triggers a cache
refresh as soon as the clock crosses CACHE_HOUR (default 9 AM).

Design notes:
  - No external dependencies — uses stdlib threading only
  - Daemon thread dies automatically when the main process exits
  - Works correctly with gunicorn multi-worker: each worker manages its
    own in-memory cache independently (existing behaviour)
  - If the DB is down at 9 AM, retries every minute until it succeeds
"""

import threading
import time
from datetime import datetime

_state = {
    "started":           False,
    "last_refresh_date": None,   # date of last successful scheduler-triggered refresh
}
_lock = threading.Lock()


def start_cache_scheduler(app) -> None:
    """
    Register and start the background refresh daemon.
    Idempotent — safe to call multiple times (only first call does anything).
    """
    with _lock:
        if _state["started"]:
            return
        _state["started"] = True

    thread = threading.Thread(
        target = _run,
        args   = (app,),
        daemon = True,
        name   = "SamarthCacheScheduler",
    )
    thread.start()
    app.logger.info(
        f"CacheScheduler: started — will auto-refresh daily at "
        f"{app.config['CACHE_HOUR']:02d}:00 (checking every 5 minutes)"
    )


# ─────────────────────────────────────────────────────────────────────────────

def _run(app) -> None:
    """Main loop. Runs inside the daemon thread indefinitely."""
    while True:
        try:
            _maybe_refresh(app)
        except Exception as exc:
            with app.app_context():
                app.logger.error(f"CacheScheduler error: {exc}")
        time.sleep(300)  # check every 5 minutes
                         # (data load itself takes 2-3 min, so 1 min was too aggressive)


def _maybe_refresh(app) -> None:
    """
    Called once per minute.
    Triggers a cache load if:
      1. Current time has reached CACHE_HOUR
      2. We haven't already refreshed today (via scheduler or user request)
    """
    with app.app_context():
        from app.services.cache_service import cache_is_fresh, refresh_data

        cache_hour = app.config["CACHE_HOUR"]
        now        = datetime.now()
        today      = now.date()

        # ── Guard 1: too early in the day ────────────────────────
        if now.hour < cache_hour:
            return

        # ── Guard 2: already done today ──────────────────────────
        if _state["last_refresh_date"] == today:
            return

        # ── Guard 3: cache is already fresh (user triggered it) ──
        if cache_is_fresh():
            _state["last_refresh_date"] = today   # mark as done
            return

        # ── Trigger scheduled refresh ─────────────────────────────
        app.logger.info(
            f"CacheScheduler: scheduled refresh at "
            f"{now:%Y-%m-%d %H:%M} (CACHE_HOUR={cache_hour})"
        )

        error = refresh_data(force=True)

        if error:
            app.logger.error(
                f"CacheScheduler: refresh failed — {error} "
                f"— will retry in 60 s"
            )
        else:
            _state["last_refresh_date"] = today
            app.logger.info("CacheScheduler: scheduled refresh succeeded")