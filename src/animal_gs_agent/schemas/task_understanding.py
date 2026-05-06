"""Schemas for model-backed task understanding."""

from typing import Literal

from pydantic import BaseModel, Field


class TaskUnderstandingResult(BaseModel):
    request_scope: Literal["supported_gs", "unsupported"]
    trait_name: str | None = None
    user_goal: str | None = None
    candidate_fixed_effects: list[str] = Field(default_factory=list)
    population_description: str | None = None
    missing_inputs: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    clarification_needed: bool

