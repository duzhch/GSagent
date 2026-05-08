"""Worker control plane schemas."""

from typing import Literal

from pydantic import BaseModel


class WorkerHealthResponse(BaseModel):
    status: Literal["ok"]
    async_run_enabled: bool
    queue_backend: str
    queue_db_path: str | None = None
    pending_jobs: int
    dead_jobs: int = 0


class WorkerQueueRecordResponse(BaseModel):
    job_id: str
    status: str
    attempts: int
    max_attempts: int
    last_error: str | None = None
    next_retry_at: str | None = None
    escalated: bool = False
    escalation_reason: str | None = None


class WorkerProcessResponse(BaseModel):
    processed: bool
    job_id: str | None = None
    job_status: str | None = None
    queue_status: str | None = None
    attempts: int | None = None
    max_attempts: int | None = None
    next_retry_at: str | None = None
    escalated: bool = False
    message: str
