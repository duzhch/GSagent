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


class PopulationStructureSummary(BaseModel):
    sample_count: int = Field(ge=0)
    pc_columns: list[str] = Field(default_factory=list)
    outlier_samples: list[str] = Field(default_factory=list)
    max_abs_zscore: float = Field(ge=0.0)
    pca_zscore_threshold: float = Field(ge=0.0)
    high_relatedness_pair_count: int = Field(ge=0)
    relatedness_threshold: float = Field(ge=0.0, le=1.0)
    related_pairs_preview: list[str] = Field(default_factory=list)
    pca_source_path: str | None = None
    relatedness_source_path: str | None = None


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
    population_structure: PopulationStructureSummary | None = None
    risk_tags: list[str] = Field(default_factory=list)
    validation_flags: list[str] = Field(default_factory=list)
