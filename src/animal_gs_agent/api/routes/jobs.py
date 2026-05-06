"""Job submission routes."""

from fastapi import APIRouter, status

from animal_gs_agent.schemas.jobs import JobSubmissionRequest, JobSubmissionResponse
from animal_gs_agent.services.job_service import create_job


def create_jobs_router() -> APIRouter:
    router = APIRouter()

    @router.post("/jobs", response_model=JobSubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
    def submit_job(payload: JobSubmissionRequest) -> JobSubmissionResponse:
        return create_job(payload)

    return router

