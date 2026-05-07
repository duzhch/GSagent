"""Minimal job service."""

from datetime import datetime, timezone
from uuid import uuid4

from animal_gs_agent.schemas.jobs import (
    JobEvent,
    JobStatusResponse,
    JobSubmissionRequest,
    JobSubmissionResponse,
)
from animal_gs_agent.schemas.dataset_profile import DatasetProfile
from animal_gs_agent.schemas.task_understanding import TaskUnderstandingResult
from animal_gs_agent.services.workflow_service import WorkflowExecutionError

jobs_store: dict[str, JobStatusResponse] = {}


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _append_event(job: JobStatusResponse, phase: str, message: str, error_code: str | None = None) -> list[JobEvent]:
    return [
        *job.events,
        JobEvent(
            phase=phase,  # type: ignore[arg-type]
            timestamp=_now_iso(),
            message=message,
            error_code=error_code,
        ),
    ]


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
        events=[
            JobEvent(
                phase="queued",
                timestamp=_now_iso(),
                message="job accepted and queued",
            )
        ],
    )
    jobs_store[job.job_id] = job
    return JobSubmissionResponse(**job.model_dump())


def get_job(job_id: str) -> JobStatusResponse | None:
    return jobs_store.get(job_id)


def run_job(job_id: str, workflow_executor=None, workflow_output_parser=None) -> JobStatusResponse | None:
    job = jobs_store.get(job_id)
    if job is None:
        return None

    running_job = job.model_copy(
        update={
            "status": "running",
            "execution_error": None,
            "execution_error_detail": None,
            "events": _append_event(job, phase="running", message="workflow execution started"),
        }
    )
    jobs_store[job_id] = running_job

    first_error = next(iter(running_job.dataset_profile.validation_flags), None)
    if first_error is not None:
        failed_job = running_job.model_copy(
            update={
                "status": "failed",
                "execution_error": first_error,
                "execution_error_detail": "dataset validation failed before workflow execution",
                "events": _append_event(
                    running_job,
                    phase="failed",
                    message="dataset validation failed",
                    error_code=first_error,
                ),
            }
        )
        jobs_store[job_id] = failed_job
        return failed_job

    if workflow_executor is not None:
        try:
            execution_result = workflow_executor(running_job)
        except WorkflowExecutionError as exc:
            failed_job = running_job.model_copy(
                update={
                    "status": "failed",
                    "execution_error": exc.code,
                    "execution_error_detail": exc.message,
                    "events": _append_event(
                        running_job,
                        phase="failed",
                        message="workflow execution failed",
                        error_code=exc.code,
                    ),
                }
            )
            jobs_store[job_id] = failed_job
            return failed_job

        workflow_summary = None
        if workflow_output_parser is not None:
            try:
                workflow_summary = workflow_output_parser(
                    result_dir=execution_result.result_dir,
                    trait_name=running_job.trait_name,
                )
            except Exception:
                failed_job = running_job.model_copy(
                    update={
                        "status": "failed",
                        "execution_error": "workflow_output_parse_error",
                        "execution_error_detail": "failed to parse fixed workflow outputs",
                        "events": _append_event(
                            running_job,
                            phase="failed",
                            message="workflow output parsing failed",
                            error_code="workflow_output_parse_error",
                        ),
                    }
                )
                jobs_store[job_id] = failed_job
                return failed_job

        completed_job = running_job.model_copy(
            update={
                "status": "completed",
                "execution_error": None,
                "execution_error_detail": None,
                "workflow_backend": execution_result.backend,
                "workflow_result_dir": execution_result.result_dir,
                "workflow_summary": workflow_summary,
                "events": _append_event(
                    running_job,
                    phase="completed",
                    message="workflow execution and parsing completed",
                ),
            }
        )
        jobs_store[job_id] = completed_job
        return completed_job

    completed_job = running_job.model_copy(
        update={
            "status": "completed",
            "execution_error": None,
            "execution_error_detail": None,
            "events": _append_event(
                running_job,
                phase="completed",
                message="job completed without external workflow executor",
            ),
        }
    )
    jobs_store[job_id] = completed_job
    return completed_job
