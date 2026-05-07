"""Schemas for dataset profiling."""

from pydantic import Field
from pydantic import BaseModel


class DatasetPathChecks(BaseModel):
    phenotype_exists: bool
    genotype_exists: bool


class DatasetProfile(BaseModel):
    phenotype_path: str
    genotype_path: str
    path_checks: DatasetPathChecks
    phenotype_format: str | None = None
    genotype_format: str | None = None
    phenotype_headers: list[str] = Field(default_factory=list)
    trait_column_present: bool | None = None
    validation_flags: list[str] = Field(default_factory=list)
