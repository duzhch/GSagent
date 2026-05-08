"""Schemas for audit claim-evidence linkage."""

from typing import Literal

from pydantic import BaseModel, Field


class ClaimEvidenceItem(BaseModel):
    claim_id: str
    claim_text: str
    evidence_links: list[str] = Field(default_factory=list)
    status: Literal["accepted", "reject"]


class AuditCheckResult(BaseModel):
    check_id: str
    status: Literal["pass", "risk"]
    evidence_links: list[str] = Field(default_factory=list)
    message: str
