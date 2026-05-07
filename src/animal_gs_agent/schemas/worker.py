"""Worker control plane schemas."""

from typing import Literal

from pydantic import BaseModel


class WorkerHealthResponse(BaseModel):
    status: Literal["ok"]
    async_run_enabled: bool
    queue_backend: str
    queue_db_path: str | None = None
    pending_jobs: int


class WorkerProcessResponse(BaseModel):
    processed: bool
    job_id: str | None = None
    job_status: str | None = None
    queue_status: str | None = None
    message: str
