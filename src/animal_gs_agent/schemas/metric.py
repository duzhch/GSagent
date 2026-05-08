"""Schemas for metric computation outputs."""

from pydantic import BaseModel, Field


class TrialMetricResult(BaseModel):
    population: str
    trait: str
    model_id: str
    pearson: float = Field(ge=-1.0, le=1.0)
    rmse: float = Field(ge=0.0)


class AggregatedMetricResult(BaseModel):
    population: str
    trait: str
    model_id: str
    trial_count: int = Field(ge=1)
    mean_pearson: float = Field(ge=-1.0, le=1.0)
    mean_rmse: float = Field(ge=0.0)


class DecisionQualityResult(BaseModel):
    selected_model_id: str
    top1_hit: bool
    regret: float | None = Field(default=None, ge=0.0)
    not_computable_reason: str | None = None


class SearchEfficiencyResult(BaseModel):
    total_trials: int = Field(ge=0)
    valid_trials: int = Field(ge=0)
    trials_to_95_best: int | None = Field(default=None, ge=1)
    invalid_trial_rate: float = Field(ge=0.0, le=1.0)
    invalid_reason_breakdown: dict[str, int] = Field(default_factory=dict)
    not_computable_reason: str | None = None
