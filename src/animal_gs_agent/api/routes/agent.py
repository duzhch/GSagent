"""Agent-facing routes."""

from fastapi import APIRouter

from animal_gs_agent.agent.task_understanding import understand_task
from animal_gs_agent.schemas.agent import ParseTaskRequest


class _NoopLLMClient:
    def request_json(self, system_prompt: str, user_prompt: str) -> dict:
        raise RuntimeError("LLM client not configured for route-level inference")


def create_agent_router() -> APIRouter:
    router = APIRouter()

    @router.post("/agent/parse-task")
    def parse_task(payload: ParseTaskRequest) -> dict:
        result = understand_task(payload.user_message, llm_client=_NoopLLMClient())
        return result.model_dump()

    return router

