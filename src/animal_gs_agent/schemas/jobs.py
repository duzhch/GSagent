"""Job request and response schemas."""

from typing import Literal

from pydantic import BaseModel, Field

from animal_gs_agent.schemas.dataset_profile import DatasetProfile
from animal_gs_agent.schemas.task_understanding import TaskUnderstandingResult


class JobSubmissionRequest(BaseModel):
    user_message: str
    trait_name: str
    phenotype_path: str
    genotype_path: str


class RankedCandidate(BaseModel):
    individual_id: str
    gebv: float
    rank: int


class WorkflowSummary(BaseModel):
    trait_name: str | None = None
    total_candidates: int
    top_candidates: list[RankedCandidate] = Field(default_factory=list)
    model_metrics: dict[str, str] = Field(default_factory=dict)
    source_files: list[str] = Field(default_factory=list)


class JobEvent(BaseModel):
    phase: Literal["queued", "running", "completed", "failed"]
    timestamp: str
    message: str
    error_code: str | None = None


class JobArtifact(BaseModel):
    relative_path: str
    size_bytes: int


class JobArtifactsResponse(BaseModel):
    job_id: str
    status: str
    artifact_count: int
    artifacts: list[JobArtifact] = Field(default_factory=list)


class JobSubmissionResponse(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    trait_name: str
    task_understanding: TaskUnderstandingResult
    dataset_profile: DatasetProfile
    execution_error: str | None = None
    execution_error_detail: str | None = None
    workflow_backend: str | None = None
    workflow_result_dir: str | None = None
    workflow_submission_id: str | None = None
    workflow_summary: WorkflowSummary | None = None
    events: list[JobEvent] = Field(default_factory=list)


class JobStatusResponse(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    trait_name: str
    task_understanding: TaskUnderstandingResult
    dataset_profile: DatasetProfile
    execution_error: str | None = None
    execution_error_detail: str | None = None
    workflow_backend: str | None = None
    workflow_result_dir: str | None = None
    workflow_submission_id: str | None = None
    workflow_summary: WorkflowSummary | None = None
    events: list[JobEvent] = Field(default_factory=list)


class JobReportResponse(BaseModel):
    job_id: str
    trait_name: str
    status: str
    report_text: str
    top_candidates: list[RankedCandidate] = Field(default_factory=list)
