"""
wsgi.py — Production entry point.

Usage with gunicorn:
    gunicorn wsgi:app --workers 4 --bind 0.0.0.0:5000

Usage with waitress (Windows):
    waitress-serve --host 0.0.0.0 --port 5000 wsgi:app
"""
import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.models.database import init_db

app = create_app("production")

# Ensure DB tables exist on startup
with app.app_context():
    init_db()