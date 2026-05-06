"""Minimal job service."""

from uuid import uuid4

from animal_gs_agent.schemas.jobs import (
    JobStatusResponse,
    JobSubmissionRequest,
    JobSubmissionResponse,
)

jobs_store: dict[str, JobStatusResponse] = {}


def create_job(payload: JobSubmissionRequest) -> JobSubmissionResponse:
    job = JobStatusResponse(
        job_id=uuid4().hex[:8],
        status="pending",
        trait_name=payload.trait_name,
    )
    jobs_store[job.job_id] = job
    return JobSubmissionResponse(**job.model_dump())


def get_job(job_id: str) -> JobStatusResponse | None:
    return jobs_store.get(job_id)
