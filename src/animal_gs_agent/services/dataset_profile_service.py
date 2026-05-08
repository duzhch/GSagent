"""Dataset profiling helpers."""

import csv
import os
from pathlib import Path

from animal_gs_agent.schemas.dataset_profile import (
    DatasetPathChecks,
    DatasetProfile,
    GenotypeMissingnessSummary,
)
from animal_gs_agent.schemas.jobs import JobSubmissionRequest

SUPPORTED_PHENOTYPE_FORMATS = {"csv", "tsv", "txt"}
SUPPORTED_GENOTYPE_FORMATS = {"pgen", "bed", "vcf"}


def _infer_format(path: str) -> str | None:
    lowered = path.lower()
    if lowered.endswith(".vcf.gz") or lowered.endswith(".vcf.bgz"):
        return "vcf"

    suffix = Path(path).suffix.lower().lstrip(".")
    return suffix or None


def _read_phenotype_headers(path: str, phenotype_format: str | None) -> list[str]:
    if phenotype_format not in SUPPORTED_PHENOTYPE_FORMATS:
        return []

    delimiter = "," if phenotype_format == "csv" else "\t"
    first_line = Path(path).read_text(encoding="utf-8").splitlines()[0]
    return [part.strip() for part in first_line.split(delimiter) if part.strip()]


def _safe_float(raw: str | None) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _read_fmiss_column(path: Path) -> list[float]:
    if not path.exists():
        return []
    values: list[float] = []
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter=" ", skipinitialspace=True)
        for row in reader:
            value = _safe_float(row.get("F_MISS"))
            if value is not None:
                values.append(value)
    return values


def _missingness_threshold() -> float:
    raw = os.getenv("ANIMAL_GS_AGENT_QC_MISSINGNESS_HIGH_THRESHOLD", "0.10")
    try:
        value = float(raw)
    except ValueError:
        return 0.10
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _build_genotype_missingness_summary() -> GenotypeMissingnessSummary | None:
    smiss_raw = os.getenv("ANIMAL_GS_AGENT_PLINK2_SMISS_PATH", "").strip()
    vmiss_raw = os.getenv("ANIMAL_GS_AGENT_PLINK2_VMISS_PATH", "").strip()
    if not smiss_raw or not vmiss_raw:
        return None

    smiss_path = Path(smiss_raw)
    vmiss_path = Path(vmiss_raw)
    sample_rates = _read_fmiss_column(smiss_path)
    variant_rates = _read_fmiss_column(vmiss_path)
    if not sample_rates or not variant_rates:
        return None

    threshold = _missingness_threshold()
    return GenotypeMissingnessSummary(
        sample_count=len(sample_rates),
        variant_count=len(variant_rates),
        sample_missing_rate_mean=sum(sample_rates) / len(sample_rates),
        sample_missing_rate_max=max(sample_rates),
        variant_missing_rate_mean=sum(variant_rates) / len(variant_rates),
        variant_missing_rate_max=max(variant_rates),
        high_risk_threshold=threshold,
        smiss_path=str(smiss_path),
        vmiss_path=str(vmiss_path),
    )


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
        # Also accept long-format phenotype tables where trait values are stored
        # in a dedicated `trait` column plus a `value` column.
        trait_column_present = "trait" in normalized_headers and "value" in normalized_headers

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

    missingness_summary = _build_genotype_missingness_summary()
    qc_risk_level: str | None = None
    if missingness_summary is not None:
        qc_risk_level = "low"
        threshold = missingness_summary.high_risk_threshold
        if (
            missingness_summary.sample_missing_rate_max > threshold
            or missingness_summary.variant_missing_rate_max > threshold
        ):
            qc_risk_level = "high"
            validation_flags.append("qc_risk_high")

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
        genotype_missingness=missingness_summary,
        qc_risk_level=qc_risk_level,
        validation_flags=validation_flags,
    )
