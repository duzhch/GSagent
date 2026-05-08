"""Worker control-plane routes."""

from fastapi import APIRouter, HTTPException

from animal_gs_agent.schemas.worker import WorkerHealthResponse, WorkerProcessResponse, WorkerQueueRecordResponse
from animal_gs_agent.services.workflow_result_service import parse_workflow_outputs
from animal_gs_agent.services.workflow_service import execute_fixed_workflow
from animal_gs_agent.services.worker_service import (
    get_worker_health_snapshot,
    get_worker_queue_record,
    process_next_queued_job,
)


def create_worker_router() -> APIRouter:
    router = APIRouter()

    @router.get("/worker/health", response_model=WorkerHealthResponse)
    def get_worker_health() -> WorkerHealthResponse:
        return get_worker_health_snapshot()

    @router.post("/worker/process-once", response_model=WorkerProcessResponse)
    def process_worker_once() -> WorkerProcessResponse:
        return process_next_queued_job(
            workflow_executor=execute_fixed_workflow,
            workflow_output_parser=parse_workflow_outputs,
        )

    @router.get("/worker/queue/{job_id}", response_model=WorkerQueueRecordResponse)
    def get_worker_queue_item(job_id: str) -> WorkerQueueRecordResponse:
        record = get_worker_queue_record(job_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Queue record for {job_id} not found")
        return record

    return router
