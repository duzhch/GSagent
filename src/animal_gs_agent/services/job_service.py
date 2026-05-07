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


def run_job(job_id: str) -> JobStatusResponse | None:
    job = jobs_store.get(job_id)
    if job is None:
        return None

    running_job = job.model_copy(update={"status": "running", "execution_error": None})
    jobs_store[job_id] = running_job

    first_error = next(iter(running_job.dataset_profile.validation_flags), None)
    if first_error is not None:
        failed_job = running_job.model_copy(update={"status": "failed", "execution_error": first_error})
        jobs_store[job_id] = failed_job
        return failed_job

    completed_job = running_job.model_copy(update={"status": "completed", "execution_error": None})
    jobs_store[job_id] = completed_job
    return completed_job
