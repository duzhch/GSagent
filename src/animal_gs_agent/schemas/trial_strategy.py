"""Schemas for trial strategy orchestration."""

from pydantic import BaseModel, Field


class TrialRecord(BaseModel):
    trial_index: int = Field(ge=1)
    model_id: str
    score: float
    is_new_best: bool


class TrialPlanResult(BaseModel):
    trials: list[TrialRecord] = Field(default_factory=list)
    selected_model: str | None = None
    budget_consumed: int = Field(ge=0)
    stop_reason: str
    random_seed: int | None = None
