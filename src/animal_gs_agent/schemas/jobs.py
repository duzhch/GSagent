"""Job request and response schemas."""

from pydantic import BaseModel

from animal_gs_agent.schemas.task_understanding import TaskUnderstandingResult


class JobSubmissionRequest(BaseModel):
    user_message: str
    trait_name: str
    phenotype_path: str
    genotype_path: str


class JobSubmissionResponse(BaseModel):
    job_id: str
    status: str
    trait_name: str
    task_understanding: TaskUnderstandingResult


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    trait_name: str
    task_understanding: TaskUnderstandingResult
