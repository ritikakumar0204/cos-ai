"""
FastAPI entrypoint.

This module wires the HTTP server, loads configuration, and prepares the
extension points (routes, orchestrator, tool registry). It intentionally
avoids business or tool-specific logic; that belongs in dedicated modules.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.project_endpoints import reset_demo_state, router as project_router
from .config import get_settings
from .routes import mcp_router, query_router, tts_router
from .tools.org_intelligence_tools import build_org_intelligence_tools
from .tools.registry import register_tool


def create_app() -> FastAPI:
    """
    Build the FastAPI application.

    Only framework and configuration wiring should live here. Do not place
    orchestrator or tool behavior inside this function—import and mount them
    instead so the app remains thin and testable.
    """

    settings = get_settings()
    reset_demo_state()

    for tool in build_org_intelligence_tools():
        try:
            register_tool(tool)
        except ValueError:
            # Keep app startup idempotent in reload/test environments.
            pass

    app = FastAPI(
        title="MCP Orchestrator",
        version=settings.version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Allow local dev frontends to call the API. Adjust origins as needed.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        """Lightweight liveness probe; does not exercise dependencies."""

        return {"status": "ok"}

    # Route registration for orchestrator and tool trace endpoints.
    app.include_router(query_router)
    app.include_router(mcp_router)
    app.include_router(tts_router)
    app.include_router(project_router)

    return app


# ASGI callable for production servers (e.g., uvicorn or gunicorn).
app = create_app()
