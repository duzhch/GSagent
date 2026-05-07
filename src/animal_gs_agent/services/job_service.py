"""Minimal job service."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
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


def _job_store_path() -> Path | None:
    raw = os.getenv("ANIMAL_GS_AGENT_JOB_STORE_PATH")
    if raw is None or not raw.strip():
        return None
    return Path(raw)


def _job_store_sqlite_path() -> Path | None:
    raw = os.getenv("ANIMAL_GS_AGENT_JOB_STORE_SQLITE_PATH")
    if raw is None or not raw.strip():
        return None
    return Path(raw)


def _sqlite_init(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _sqlite_load(path: Path) -> dict[str, JobStatusResponse]:
    _sqlite_init(path)
    loaded: dict[str, JobStatusResponse] = {}
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT job_id, payload FROM jobs").fetchall()
    for job_id, payload in rows:
        loaded[job_id] = JobStatusResponse.model_validate_json(payload)
    return loaded


def _sqlite_persist(path: Path) -> None:
    _sqlite_init(path)
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM jobs")
        conn.executemany(
            "INSERT INTO jobs(job_id, payload) VALUES(?, ?)",
            [(job_id, job.model_dump_json()) for job_id, job in jobs_store.items()],
        )
        conn.commit()


def _load_store_if_needed() -> None:
    if jobs_store:
        return
    sqlite_path = _job_store_sqlite_path()
    if sqlite_path is not None:
        jobs_store.update(_sqlite_load(sqlite_path))
        return
    path = _job_store_path()
    if path is None or not path.exists():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    for job_id, raw in payload.items():
        jobs_store[job_id] = JobStatusResponse.model_validate(raw)


def _persist_store_if_needed() -> None:
    sqlite_path = _job_store_sqlite_path()
    if sqlite_path is not None:
        _sqlite_persist(sqlite_path)
        return
    path = _job_store_path()
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {job_id: job.model_dump() for job_id, job in jobs_store.items()}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


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
    _persist_store_if_needed()
    return JobSubmissionResponse(**job.model_dump())


def get_job(job_id: str) -> JobStatusResponse | None:
    _load_store_if_needed()
    return jobs_store.get(job_id)


def refresh_running_job(
    job_id: str,
    slurm_state_checker=None,
    workflow_output_parser=None,
) -> JobStatusResponse | None:
    job = jobs_store.get(job_id)
    if job is None:
        return None
    if job.status != "running":
        return job
    if job.workflow_backend != "slurm_nextflow_submit":
        return job
    if not job.workflow_submission_id:
        return job
    if slurm_state_checker is None:
        return job

    queue_state = slurm_state_checker(job.workflow_submission_id)
    if queue_state in {"PENDING", "RUNNING", "UNKNOWN"}:
        updated = job.model_copy(
            update={
                "workflow_queue_state": queue_state,
            }
        )
        jobs_store[job_id] = updated
        _persist_store_if_needed()
        return updated

    if queue_state == "COMPLETED":
        workflow_summary = None
        if workflow_output_parser is not None and job.workflow_result_dir:
            try:
                workflow_summary = workflow_output_parser(
                    result_dir=job.workflow_result_dir,
                    trait_name=job.trait_name,
                )
            except Exception:
                failed = job.model_copy(
                    update={
                        "status": "failed",
                        "workflow_queue_state": queue_state,
                        "execution_error": "workflow_output_parse_error",
                        "execution_error_detail": "failed to parse fixed workflow outputs",
                        "events": _append_event(
                            job,
                            phase="failed",
                            message="workflow output parsing failed after slurm completion",
                            error_code="workflow_output_parse_error",
                        ),
                    }
                )
                jobs_store[job_id] = failed
                _persist_store_if_needed()
                return failed

        completed = job.model_copy(
            update={
                "status": "completed",
                "workflow_queue_state": queue_state,
                "execution_error": None,
                "execution_error_detail": None,
                "workflow_summary": workflow_summary,
                "events": _append_event(
                    job,
                    phase="completed",
                    message=f"slurm workflow finished ({queue_state})",
                ),
            }
        )
        jobs_store[job_id] = completed
        _persist_store_if_needed()
        return completed

    failed = job.model_copy(
        update={
            "status": "failed",
            "workflow_queue_state": queue_state,
            "execution_error": "workflow_slurm_failed",
            "execution_error_detail": f"slurm job state: {queue_state}",
            "events": _append_event(
                job,
                phase="failed",
                message=f"slurm workflow failed ({queue_state})",
                error_code="workflow_slurm_failed",
            ),
        }
    )
    jobs_store[job_id] = failed
    _persist_store_if_needed()
    return failed


def run_job(job_id: str, workflow_executor=None, workflow_output_parser=None) -> JobStatusResponse | None:
    _load_store_if_needed()
    job = jobs_store.get(job_id)
    if job is None:
        return None
    if job.status in {"running", "completed"}:
        return job

    running_job = job.model_copy(
        update={
            "status": "running",
            "execution_error": None,
            "execution_error_detail": None,
            "events": _append_event(job, phase="running", message="workflow execution started"),
        }
    )
    jobs_store[job_id] = running_job
    _persist_store_if_needed()

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
        _persist_store_if_needed()
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
            _persist_store_if_needed()
            return failed_job

        if execution_result.status == "submitted":
            submitted_job = running_job.model_copy(
                update={
                    "status": "running",
                    "execution_error": None,
                    "execution_error_detail": None,
                    "workflow_backend": execution_result.backend,
                    "workflow_result_dir": execution_result.result_dir,
                    "workflow_submission_id": execution_result.submission_id,
                    "workflow_queue_state": "PENDING",
                    "events": _append_event(
                        running_job,
                        phase="running",
                        message=f"submitted workflow to slurm ({execution_result.submission_id or 'unknown_job_id'})",
                    ),
                }
            )
            jobs_store[job_id] = submitted_job
            _persist_store_if_needed()
            return submitted_job

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
                _persist_store_if_needed()
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
        _persist_store_if_needed()
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
    _persist_store_if_needed()
    return completed_job
