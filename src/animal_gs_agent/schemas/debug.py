"""Schemas for debug diagnosis and retry guidance."""

from typing import Literal

from pydantic import BaseModel, Field


DebugFailureCategory = Literal["environment", "data", "code", "resource"]
DebugRetryDecision = Literal["retry", "escalate"]


class DebugDiagnosis(BaseModel):
    category: DebugFailureCategory
    retryable: bool
    suggested_retry_decision: DebugRetryDecision
    suggested_action: str = Field(min_length=1)
    attempt: int = Field(ge=1)
    max_attempts: int = Field(ge=1)
    escalate_immediately: bool
