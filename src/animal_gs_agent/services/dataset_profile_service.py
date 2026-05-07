"""Dataset profiling helpers."""

from pathlib import Path

from animal_gs_agent.schemas.dataset_profile import DatasetPathChecks, DatasetProfile
from animal_gs_agent.schemas.jobs import JobSubmissionRequest


def build_dataset_profile(payload: JobSubmissionRequest) -> DatasetProfile:
    return DatasetProfile(
        phenotype_path=payload.phenotype_path,
        genotype_path=payload.genotype_path,
        path_checks=DatasetPathChecks(
            phenotype_exists=Path(payload.phenotype_path).exists(),
            genotype_exists=Path(payload.genotype_path).exists(),
        ),
    )

