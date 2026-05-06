"""FastAPI application factory."""

from fastapi import FastAPI

from animal_gs_agent.api.routes.health import create_health_router


def create_app() -> FastAPI:
    app = FastAPI(title="Animal GS Agent")
    app.include_router(create_health_router())
    return app

