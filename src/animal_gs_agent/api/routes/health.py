"""Health route."""

from fastapi import APIRouter

from animal_gs_agent.config import get_settings


def create_health_router() -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def healthcheck() -> dict[str, str]:
        settings = get_settings()
        return {"service": settings.service_name, "status": "ok"}

    return router
