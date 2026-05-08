"""Schemas for benchmark, ablation, and plot export artifacts."""

from typing import Literal

from pydantic import BaseModel, Field


class BenchmarkArmResult(BaseModel):
    arm_id: Literal["single_agent", "react_agent", "multi_agent"]
    pearson: float
    rmse: float = Field(ge=0.0)
    regret: float = Field(ge=0.0)


class BaselineBenchmarkReport(BaseModel):
    compared_arms: list[BenchmarkArmResult] = Field(default_factory=list)
    winner_arm_id: Literal["single_agent", "react_agent", "multi_agent"]
    reproducibility_tag: str


class AblationBenchmarkItem(BaseModel):
    ablation_name: str
    delta_pearson: float
    delta_rmse: float
    impact_label: Literal["minor", "moderate", "major"]


class PlotExportArtifact(BaseModel):
    format: Literal["csv"]
    artifact_path: str
