"""
run.py — Development server entry point.
Never use this in production — use wsgi.py with gunicorn instead.

Usage:
    python run.py
"""
import os
from dotenv import load_dotenv

load_dotenv()   # must happen before create_app reads os.environ

from app import create_app
from app.models.database import init_db

app = create_app("development")

if __name__ == "__main__":
    # Ensure DB tables exist on every dev startup
    with app.app_context():
        init_db()
        print("\n🚀 Heritage Samarth is running!")
        print(f"📅 Cache window: from {app.config['CACHE_HOUR']}:00 AM daily")
        print(f"🗄️  Database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'SQLite (samarth.db)')}")
        print(f"🌐 URL: http://localhost:5000\n")

    app.run(
        debug = True,
        host  = "0.0.0.0",
        port  = 5000,
    )