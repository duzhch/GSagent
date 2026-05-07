"""Worker control-plane helpers."""

from __future__ import annotations

import os

from animal_gs_agent.schemas.worker import WorkerHealthResponse, WorkerProcessResponse
from animal_gs_agent.services.job_service import run_job
from animal_gs_agent.services.run_queue_service import (
    claim_next_run_job,
    count_pending_jobs,
    get_run_queue_record,
    mark_run_job_done,
    mark_run_job_failed,
)
from animal_gs_agent.services.workflow_result_service import parse_workflow_outputs
from animal_gs_agent.services.workflow_service import execute_fixed_workflow


def _async_enabled() -> bool:
    return os.getenv("ANIMAL_GS_AGENT_ASYNC_RUN_ENABLED", "").strip().lower() in {"1", "true", "yes"}


def get_worker_health_snapshot() -> WorkerHealthResponse:
    queue_path = os.getenv("ANIMAL_GS_AGENT_RUN_QUEUE_SQLITE_PATH")
    if not queue_path or not queue_path.strip():
        job_store_path = os.getenv("ANIMAL_GS_AGENT_JOB_STORE_SQLITE_PATH")
        if job_store_path and job_store_path.strip():
            queue_path = os.path.join(os.path.dirname(job_store_path), "run_queue.db")
        else:
            queue_path = "/tmp/animal_gs_agent_run_queue.db"

    return WorkerHealthResponse(
        status="ok",
        async_run_enabled=_async_enabled(),
        queue_backend="sqlite",
        queue_db_path=queue_path,
        pending_jobs=count_pending_jobs(),
    )


def process_next_queued_job(
    workflow_executor=None,
    workflow_output_parser=None,
) -> WorkerProcessResponse:
    if workflow_executor is None:
        workflow_executor = execute_fixed_workflow
    if workflow_output_parser is None:
        workflow_output_parser = parse_workflow_outputs

    job_id = claim_next_run_job()
    if job_id is None:
        return WorkerProcessResponse(
            processed=False,
            message="no pending jobs",
            queue_status="idle",
        )

    try:
        job = run_job(
            job_id,
            workflow_executor=workflow_executor,
            workflow_output_parser=workflow_output_parser,
        )
        if job is None:
            mark_run_job_failed(job_id, "job_not_found")
            return WorkerProcessResponse(
                processed=True,
                job_id=job_id,
                job_status="missing",
                queue_status="failed",
                message="job not found in store",
            )

        if job.status == "failed":
            mark_run_job_failed(job_id, job.execution_error or "workflow_failed")
            return WorkerProcessResponse(
                processed=True,
                job_id=job_id,
                job_status=job.status,
                queue_status="failed",
                message=job.execution_error_detail or job.execution_error or "workflow failed",
            )

        mark_run_job_done(job_id)
        return WorkerProcessResponse(
            processed=True,
            job_id=job_id,
            job_status=job.status,
            queue_status="done",
            message="job processed by worker",
        )
    except Exception as exc:
        mark_run_job_failed(job_id, str(exc))
        return WorkerProcessResponse(
            processed=True,
            job_id=job_id,
            job_status="failed",
            queue_status="failed",
            message=str(exc),
        )
