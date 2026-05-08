"""Schemas for knowledge retrieval and citation output."""

from typing import Literal

from pydantic import BaseModel, Field


KnowledgeSourceType = Literal["historical_task", "sop", "literature"]


class KnowledgeDocument(BaseModel):
    source_id: str
    source_type: KnowledgeSourceType
    title: str
    content: str


class RetrievedEvidence(BaseModel):
    source_id: str
    source_type: KnowledgeSourceType
    title: str
    snippet: str
    score: float = Field(ge=0.0)


class RecommendationCitation(BaseModel):
    recommendation: str
    evidence: list[RetrievedEvidence] = Field(default_factory=list)
    conflict: bool = False
    conflict_note: str | None = None
