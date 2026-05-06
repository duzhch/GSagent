"""Job submission routes."""

from fastapi import APIRouter, HTTPException, status

from animal_gs_agent.schemas.jobs import (
    JobStatusResponse,
    JobSubmissionRequest,
    JobSubmissionResponse,
)
from animal_gs_agent.services.job_service import create_job, get_job


def create_jobs_router() -> APIRouter:
    router = APIRouter()

    @router.post("/jobs", response_model=JobSubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
    def submit_job(payload: JobSubmissionRequest) -> JobSubmissionResponse:
        return create_job(payload)

    @router.get("/jobs/{job_id}", response_model=JobStatusResponse)
    def get_job_status(job_id: str) -> JobStatusResponse:
        job = get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        return job

    return router
