"""Vercel serverless function entry point for the FastAPI backend."""
import sys
import os

# Add the backend directory to the Python path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Set VERCEL env var if not already set (for detecting serverless environment)
os.environ.setdefault("VERCEL", "1")

from app.main import app  # noqa: E402 — path must be set first

# Vercel's Python runtime looks for an `app` variable (ASGI/WSGI)
# The FastAPI `app` is already ASGI-compatible, so this just works.
