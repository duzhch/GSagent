"""FastAPI application factory."""

from fastapi import Depends, FastAPI

from animal_gs_agent.api.auth import require_api_token
from animal_gs_agent.api.routes.agent import create_agent_router
from animal_gs_agent.api.routes.health import create_health_router
from animal_gs_agent.api.routes.jobs import create_jobs_router
from animal_gs_agent.api.routes.worker import create_worker_router


def create_app() -> FastAPI:
    app = FastAPI(title="Animal GS Agent")
    app.include_router(create_health_router())
    protected = [Depends(require_api_token)]
    app.include_router(create_agent_router(), dependencies=protected)
    app.include_router(create_jobs_router(), dependencies=protected)
    app.include_router(create_worker_router(), dependencies=protected)
    return app
