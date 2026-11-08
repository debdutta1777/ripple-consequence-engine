"""Vercel FastAPI entrypoint for Ripple.

The app code lives in app/main.py so the same application runs locally
with `uvicorn app.main:app` and on Vercel with FastAPI detection.
"""
from app.main import app

__all__ = ["app"]
