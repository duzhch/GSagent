"""Job submission routes."""

from fastapi import APIRouter, HTTPException, status

from animal_gs_agent.agent.task_understanding import (
    TaskUnderstandingProviderError,
    TaskUnderstandingValidationError,
    understand_task,
)
from animal_gs_agent.config import get_settings
from animal_gs_agent.llm.client import OpenAICompatibleLLMClient
from animal_gs_agent.schemas.jobs import (
    JobStatusResponse,
    JobSubmissionRequest,
    JobSubmissionResponse,
)
from animal_gs_agent.services.dataset_profile_service import build_dataset_profile
from animal_gs_agent.services.job_service import create_job, get_job


def create_jobs_router() -> APIRouter:
    router = APIRouter()

    @router.post("/jobs", response_model=JobSubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
    def submit_job(payload: JobSubmissionRequest) -> JobSubmissionResponse:
        settings = get_settings()
        if not settings.llm.base_url or not settings.llm.api_key or not settings.llm.model:
            raise HTTPException(status_code=503, detail="LLM provider is not configured")

        client = OpenAICompatibleLLMClient(settings.llm)
        try:
            task_understanding = understand_task(payload.user_message, llm_client=client)
        except (TaskUnderstandingProviderError, TaskUnderstandingValidationError) as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        dataset_profile = build_dataset_profile(payload)
        return create_job(
            payload,
            task_understanding=task_understanding,
            dataset_profile=dataset_profile,
        )

    @router.get("/jobs/{job_id}", response_model=JobStatusResponse)
    def get_job_status(job_id: str) -> JobStatusResponse:
        job = get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        return job

    return router
