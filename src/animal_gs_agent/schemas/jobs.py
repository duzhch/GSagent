"""Job request and response schemas."""

from pydantic import BaseModel


class JobSubmissionRequest(BaseModel):
    user_message: str
    trait_name: str
    phenotype_path: str
    genotype_path: str


class JobSubmissionResponse(BaseModel):
    job_id: str
    status: str
    trait_name: str

