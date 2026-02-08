"""
Route package exports.

Only re-export routers to keep import surfaces predictable.
"""

from .mcp import router as mcp_router
from .query import router as query_router
from .tts import router as tts_router

__all__ = ["query_router", "mcp_router", "tts_router"]
