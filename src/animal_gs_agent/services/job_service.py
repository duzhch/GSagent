"""Minimal job service."""

from uuid import uuid4

from animal_gs_agent.schemas.jobs import (
    JobStatusResponse,
    JobSubmissionRequest,
    JobSubmissionResponse,
)
from animal_gs_agent.schemas.dataset_profile import DatasetProfile
from animal_gs_agent.schemas.task_understanding import TaskUnderstandingResult

jobs_store: dict[str, JobStatusResponse] = {}


def create_job(
    payload: JobSubmissionRequest,
    task_understanding: TaskUnderstandingResult,
    dataset_profile: DatasetProfile,
) -> JobSubmissionResponse:
    job = JobStatusResponse(
        job_id=uuid4().hex[:8],
        status="queued",
        trait_name=payload.trait_name,
        task_understanding=task_understanding,
        dataset_profile=dataset_profile,
    )
    jobs_store[job.job_id] = job
    return JobSubmissionResponse(**job.model_dump())


def get_job(job_id: str) -> JobStatusResponse | None:
    return jobs_store.get(job_id)
