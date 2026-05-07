"""Job request and response schemas."""

from typing import Literal

from pydantic import BaseModel

from animal_gs_agent.schemas.dataset_profile import DatasetProfile
from animal_gs_agent.schemas.task_understanding import TaskUnderstandingResult


class JobSubmissionRequest(BaseModel):
    user_message: str
    trait_name: str
    phenotype_path: str
    genotype_path: str


class JobSubmissionResponse(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    trait_name: str
    task_understanding: TaskUnderstandingResult
    dataset_profile: DatasetProfile
    execution_error: str | None = None
    workflow_backend: str | None = None
    workflow_result_dir: str | None = None


class JobStatusResponse(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    trait_name: str
    task_understanding: TaskUnderstandingResult
    dataset_profile: DatasetProfile
    execution_error: str | None = None
    workflow_backend: str | None = None
    workflow_result_dir: str | None = None
