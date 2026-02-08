"""
Application package initializer.

Exports the ASGI app and factory for convenience while keeping package-level
side effects to a minimum.
"""

from .main import app, create_app

__all__ = ["app", "create_app"]
