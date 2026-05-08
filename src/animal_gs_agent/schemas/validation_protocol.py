"""Schemas for scenario-based validation protocol planning."""

from pydantic import BaseModel, Field


class ValidationSplitRecord(BaseModel):
    split_id: str
    train_population: str
    validation_population: str
    notes: str | None = None


class ScenarioValidationProtocol(BaseModel):
    scenario_id: str
    split_records: list[ValidationSplitRecord] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)


class ValidationProtocolPlan(BaseModel):
    protocols: list[ScenarioValidationProtocol] = Field(default_factory=list)
