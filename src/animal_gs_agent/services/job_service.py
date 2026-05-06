"""Minimal job service."""

from uuid import uuid4

from animal_gs_agent.schemas.jobs import (
    JobSubmissionRequest,
    JobSubmissionResponse,
)


def create_job(payload: JobSubmissionRequest) -> JobSubmissionResponse:
    return JobSubmissionResponse(
        job_id=uuid4().hex[:8],
        status="pending",
        trait_name=payload.trait_name,
    )

