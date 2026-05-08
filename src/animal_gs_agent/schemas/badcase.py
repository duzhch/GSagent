"""Schemas for badcase memory and preventive guidance."""

from pydantic import BaseModel, Field


class BadcaseRecord(BaseModel):
    job_id: str
    trait_name: str
    population_description: str
    risk_tags: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    status: str
    summary: str


class SimilarBadcaseMatch(BaseModel):
    record: BadcaseRecord
    similarity: float = Field(ge=0.0, le=1.0)


class BadcaseAdvice(BaseModel):
    queried: bool
    high_similarity_hit: bool
    similar_cases: list[SimilarBadcaseMatch] = Field(default_factory=list)
    preventive_actions: list[str] = Field(default_factory=list)
