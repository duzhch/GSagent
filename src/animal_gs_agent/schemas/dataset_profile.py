"""Schemas for dataset profiling."""

from pydantic import BaseModel


class DatasetPathChecks(BaseModel):
    phenotype_exists: bool
    genotype_exists: bool


class DatasetProfile(BaseModel):
    phenotype_path: str
    genotype_path: str
    path_checks: DatasetPathChecks

