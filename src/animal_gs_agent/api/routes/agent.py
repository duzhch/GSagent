"""Agent-facing routes."""

from fastapi import APIRouter, HTTPException

from animal_gs_agent.agent.task_understanding import (
    TaskUnderstandingProviderError,
    TaskUnderstandingValidationError,
    understand_task,
)
from animal_gs_agent.config import get_settings
from animal_gs_agent.llm.client import OpenAICompatibleLLMClient
from animal_gs_agent.schemas.agent import ParseTaskRequest


def create_agent_router() -> APIRouter:
    router = APIRouter()

    @router.post("/agent/parse-task")
    def parse_task(payload: ParseTaskRequest) -> dict:
        settings = get_settings()
        if not settings.llm.base_url or not settings.llm.api_key or not settings.llm.model:
            raise HTTPException(status_code=503, detail="LLM provider is not configured")

        client = OpenAICompatibleLLMClient(settings.llm)
        try:
            result = understand_task(payload.user_message, llm_client=client)
        except (TaskUnderstandingProviderError, TaskUnderstandingValidationError) as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return result.model_dump()

    return router
