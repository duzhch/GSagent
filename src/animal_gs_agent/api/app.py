"""FastAPI application factory."""

from fastapi import FastAPI

from animal_gs_agent.api.routes.agent import create_agent_router
from animal_gs_agent.api.routes.health import create_health_router
from animal_gs_agent.api.routes.jobs import create_jobs_router


def create_app() -> FastAPI:
    app = FastAPI(title="Animal GS Agent")
    app.include_router(create_agent_router())
    app.include_router(create_health_router())
    app.include_router(create_jobs_router())
    return app
