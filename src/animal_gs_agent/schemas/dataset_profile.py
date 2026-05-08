"""Schemas for dataset profiling."""

from pydantic import Field
from pydantic import BaseModel


class DatasetPathChecks(BaseModel):
    phenotype_exists: bool
    genotype_exists: bool


class GenotypeMissingnessSummary(BaseModel):
    sample_count: int = Field(ge=0)
    variant_count: int = Field(ge=0)
    sample_missing_rate_mean: float = Field(ge=0.0, le=1.0)
    sample_missing_rate_max: float = Field(ge=0.0, le=1.0)
    variant_missing_rate_mean: float = Field(ge=0.0, le=1.0)
    variant_missing_rate_max: float = Field(ge=0.0, le=1.0)
    high_risk_threshold: float = Field(ge=0.0, le=1.0)
    smiss_path: str | None = None
    vmiss_path: str | None = None


class DatasetProfile(BaseModel):
    phenotype_path: str
    genotype_path: str
    path_checks: DatasetPathChecks
    phenotype_format: str | None = None
    genotype_format: str | None = None
    phenotype_headers: list[str] = Field(default_factory=list)
    trait_column_present: bool | None = None
    genotype_missingness: GenotypeMissingnessSummary | None = None
    qc_risk_level: str | None = None
    validation_flags: list[str] = Field(default_factory=list)
