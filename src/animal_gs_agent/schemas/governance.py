"""Schemas for governance controls and observability audit snapshots."""

from pydantic import BaseModel, Field


class GovernanceAuditResponse(BaseModel):
    job_id: str
    execution_status: str
    project_scope: str
    requested_by: str
    event_count: int = Field(ge=0)
    decision_count: int = Field(ge=0)
    escalation_seen: bool
    latest_error_code: str | None = None
