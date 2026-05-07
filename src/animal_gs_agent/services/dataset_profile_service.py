"""Dataset profiling helpers."""

from pathlib import Path

from animal_gs_agent.schemas.dataset_profile import DatasetPathChecks, DatasetProfile
from animal_gs_agent.schemas.jobs import JobSubmissionRequest

SUPPORTED_PHENOTYPE_FORMATS = {"csv", "tsv", "txt"}
SUPPORTED_GENOTYPE_FORMATS = {"pgen", "bed", "vcf"}


def _infer_format(path: str) -> str | None:
    suffix = Path(path).suffix.lower().lstrip(".")
    return suffix or None


def _read_phenotype_headers(path: str, phenotype_format: str | None) -> list[str]:
    if phenotype_format not in SUPPORTED_PHENOTYPE_FORMATS:
        return []

    delimiter = "," if phenotype_format == "csv" else "\t"
    first_line = Path(path).read_text(encoding="utf-8").splitlines()[0]
    return [part.strip() for part in first_line.split(delimiter) if part.strip()]


def build_dataset_profile(payload: JobSubmissionRequest) -> DatasetProfile:
    phenotype_path = Path(payload.phenotype_path)
    genotype_path = Path(payload.genotype_path)
    phenotype_exists = phenotype_path.exists()
    genotype_exists = genotype_path.exists()
    phenotype_format = _infer_format(payload.phenotype_path)
    genotype_format = _infer_format(payload.genotype_path)

    phenotype_headers: list[str] = []
    if phenotype_exists:
        try:
            phenotype_headers = _read_phenotype_headers(payload.phenotype_path, phenotype_format)
        except (OSError, IndexError, UnicodeDecodeError):
            phenotype_headers = []

    normalized_headers = {header.lower() for header in phenotype_headers}
    trait_column_present = payload.trait_name.lower() in normalized_headers if phenotype_headers else None
    if phenotype_headers and payload.trait_name.lower() not in normalized_headers:
        trait_column_present = False

    validation_flags: list[str] = []
    if not phenotype_exists:
        validation_flags.append("phenotype_not_found")
    if not genotype_exists:
        validation_flags.append("genotype_not_found")
    if phenotype_format and phenotype_format not in SUPPORTED_PHENOTYPE_FORMATS:
        validation_flags.append("phenotype_format_unsupported")
    if genotype_format and genotype_format not in SUPPORTED_GENOTYPE_FORMATS:
        validation_flags.append("genotype_format_unsupported")
    if trait_column_present is False:
        validation_flags.append("trait_column_missing")

    return DatasetProfile(
        phenotype_path=payload.phenotype_path,
        genotype_path=payload.genotype_path,
        path_checks=DatasetPathChecks(
            phenotype_exists=phenotype_exists,
            genotype_exists=genotype_exists,
        ),
        phenotype_format=phenotype_format,
        genotype_format=genotype_format,
        phenotype_headers=phenotype_headers,
        trait_column_present=trait_column_present,
        validation_flags=validation_flags,
    )
