"""Schemas for model-pool planning."""

from pydantic import BaseModel, Field


class ModelCandidatePlan(BaseModel):
    model_id: str
    available: bool
    disabled_reasons: list[str] = Field(default_factory=list)


class ModelPoolPlan(BaseModel):
    candidates: list[ModelCandidatePlan] = Field(default_factory=list)
    available_models: list[str] = Field(default_factory=list)
