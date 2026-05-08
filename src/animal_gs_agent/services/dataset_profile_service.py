"""Dataset profiling helpers."""

import csv
import math
import os
from pathlib import Path

from animal_gs_agent.schemas.dataset_profile import (
    DatasetPathChecks,
    DatasetProfile,
    GenotypeMissingnessSummary,
    PhenotypeDiagnosticsSummary,
    PopulationStructureSummary,
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


def _safe_threshold(raw: str, default: float, *, min_value: float, max_value: float) -> float:
    try:
        value = float(raw)
    except ValueError:
        return default
    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value


def _pca_outlier_threshold() -> float:
    raw = os.getenv("ANIMAL_GS_AGENT_QC_PCA_ZSCORE_THRESHOLD", "3.0")
    return _safe_threshold(raw, 3.0, min_value=0.0, max_value=100.0)


def _relatedness_threshold() -> float:
    raw = os.getenv("ANIMAL_GS_AGENT_QC_RELATEDNESS_HIGH_THRESHOLD", "0.25")
    return _safe_threshold(raw, 0.25, min_value=0.0, max_value=1.0)


def _pheno_outlier_zscore_threshold() -> float:
    raw = os.getenv("ANIMAL_GS_AGENT_PHENO_OUTLIER_ZSCORE_THRESHOLD", "3.0")
    return _safe_threshold(raw, 3.0, min_value=0.0, max_value=100.0)


def _pheno_outlier_high_ratio_threshold() -> float:
    raw = os.getenv("ANIMAL_GS_AGENT_PHENO_OUTLIER_HIGH_RATIO_THRESHOLD", "0.10")
    return _safe_threshold(raw, 0.10, min_value=0.0, max_value=1.0)


def _pheno_batch_effect_eta2_threshold() -> float:
    raw = os.getenv("ANIMAL_GS_AGENT_PHENO_BATCH_EFFECT_MIN_ETA2", "0.20")
    return _safe_threshold(raw, 0.20, min_value=0.0, max_value=1.0)


def _pheno_batch_column() -> str:
    raw = os.getenv("ANIMAL_GS_AGENT_PHENO_BATCH_COLUMN", "batch").strip()
    return raw or "batch"


def _split_row(line: str) -> list[str]:
    return [part for part in line.strip().split() if part]


def _parse_eigenvec(path: Path) -> tuple[list[str], list[str], list[list[float]]]:
    if not path.exists():
        return [], [], []
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return [], [], []

    first_tokens = _split_row(lines[0])
    has_header = any(token.upper().startswith("PC") for token in first_tokens)

    rows: list[list[str]] = []
    header: list[str]
    if has_header:
        header = [token.lstrip("#") for token in first_tokens]
        rows = [_split_row(line) for line in lines[1:]]
    else:
        token_count = len(first_tokens)
        if token_count < 3:
            return [], [], []
        header = ["FID", "IID"] + [f"PC{i}" for i in range(1, token_count - 1)]
        rows = [first_tokens] + [_split_row(line) for line in lines[1:]]

    pc_columns = [col for col in header if col.upper().startswith("PC")]
    if not pc_columns:
        return [], [], []

    sample_ids: list[str] = []
    pc_values: list[list[float]] = []
    for row in rows:
        if len(row) < len(header):
            continue
        row_map = {header[i]: row[i] for i in range(len(header))}
        iid = row_map.get("IID")
        if not iid:
            continue
        values: list[float] = []
        valid = True
        for pc in pc_columns:
            value = _safe_float(row_map.get(pc))
            if value is None:
                valid = False
                break
            values.append(value)
        if not valid:
            continue
        sample_ids.append(iid)
        pc_values.append(values)

    return pc_columns, sample_ids, pc_values


def _compute_outliers(pc_values: list[list[float]], zscore_threshold: float) -> tuple[list[bool], float]:
    if not pc_values:
        return [], 0.0
    dims = len(pc_values[0])
    means = [sum(row[i] for row in pc_values) / len(pc_values) for i in range(dims)]
    stds: list[float] = []
    for i in range(dims):
        variance = sum((row[i] - means[i]) ** 2 for row in pc_values) / len(pc_values)
        stds.append(math.sqrt(variance))

    outlier_flags: list[bool] = []
    max_abs_zscore = 0.0
    for row in pc_values:
        row_max_abs = 0.0
        for i, value in enumerate(row):
            if stds[i] == 0:
                z = 0.0
            else:
                z = abs((value - means[i]) / stds[i])
            row_max_abs = max(row_max_abs, z)
            max_abs_zscore = max(max_abs_zscore, z)
        outlier_flags.append(row_max_abs > zscore_threshold)
    return outlier_flags, max_abs_zscore


def _parse_relatedness(path: Path, threshold: float) -> tuple[int, list[str]]:
    if not path.exists():
        return 0, []
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) < 2:
        return 0, []
    header = _split_row(lines[0])
    kinship_col = "PI_HAT" if "PI_HAT" in header else ("KINSHIP" if "KINSHIP" in header else None)
    if kinship_col is None:
        return 0, []

    high_count = 0
    preview: list[str] = []
    for line in lines[1:]:
        row = _split_row(line)
        if len(row) < len(header):
            continue
        row_map = {header[i]: row[i] for i in range(len(header))}
        metric = _safe_float(row_map.get(kinship_col))
        if metric is None or metric <= threshold:
            continue
        iid1 = row_map.get("IID1", "unknown1")
        iid2 = row_map.get("IID2", "unknown2")
        high_count += 1
        if len(preview) < 10:
            preview.append(f"{iid1}-{iid2}({metric:.3f})")
    return high_count, preview


def _build_population_structure_summary() -> PopulationStructureSummary | None:
    pca_raw = os.getenv("ANIMAL_GS_AGENT_PLINK2_PCA_EIGENVEC_PATH", "").strip()
    related_raw = os.getenv("ANIMAL_GS_AGENT_PLINK2_RELATEDNESS_PATH", "").strip()
    if not pca_raw and not related_raw:
        return None

    pca_path = Path(pca_raw) if pca_raw else None
    related_path = Path(related_raw) if related_raw else None
    z_threshold = _pca_outlier_threshold()
    rel_threshold = _relatedness_threshold()

    pc_columns: list[str] = []
    sample_ids: list[str] = []
    pc_values: list[list[float]] = []
    if pca_path is not None:
        pc_columns, sample_ids, pc_values = _parse_eigenvec(pca_path)
    outlier_flags, max_abs_zscore = _compute_outliers(pc_values, z_threshold)
    outlier_samples = [sample_ids[idx] for idx, flagged in enumerate(outlier_flags) if flagged]

    high_related_count = 0
    related_preview: list[str] = []
    if related_path is not None:
        high_related_count, related_preview = _parse_relatedness(related_path, rel_threshold)

    if not sample_ids and high_related_count == 0:
        return None

    return PopulationStructureSummary(
        sample_count=len(sample_ids),
        pc_columns=pc_columns,
        outlier_samples=outlier_samples,
        max_abs_zscore=max_abs_zscore,
        pca_zscore_threshold=z_threshold,
        high_relatedness_pair_count=high_related_count,
        relatedness_threshold=rel_threshold,
        related_pairs_preview=related_preview,
        pca_source_path=str(pca_path) if pca_path is not None else None,
        relatedness_source_path=str(related_path) if related_path is not None else None,
    )


def _iter_phenotype_rows(path: Path, phenotype_format: str | None) -> list[dict[str, str]]:
    if phenotype_format not in SUPPORTED_PHENOTYPE_FORMATS:
        return []
    delimiter = "," if phenotype_format == "csv" else "\t"
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        return [{k.strip(): (v.strip() if isinstance(v, str) else "") for k, v in row.items()} for row in reader]


def _extract_trait_and_batch_values(
    rows: list[dict[str, str]], trait_name: str, batch_column: str
) -> tuple[list[float], list[str]]:
    if not rows:
        return [], []
    if trait_name in rows[0]:
        trait_values: list[float] = []
        batches: list[str] = []
        for row in rows:
            value = _safe_float(row.get(trait_name))
            if value is None:
                continue
            trait_values.append(value)
            batches.append(row.get(batch_column, ""))
        return trait_values, batches

    has_long_format = "trait" in rows[0] and "value" in rows[0]
    if not has_long_format:
        return [], []
    trait_values = []
    batches = []
    for row in rows:
        if row.get("trait", "") != trait_name:
            continue
        value = _safe_float(row.get("value"))
        if value is None:
            continue
        trait_values.append(value)
        batches.append(row.get(batch_column, ""))
    return trait_values, batches


def _compute_outlier_count(values: list[float], zscore_threshold: float) -> int:
    if len(values) < 2:
        return 0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    std = math.sqrt(variance)
    if std == 0:
        return 0
    return sum(1 for value in values if abs((value - mean) / std) > zscore_threshold)


def _compute_batch_eta2(values: list[float], batches: list[str]) -> tuple[float, int]:
    paired = [(value, batch) for value, batch in zip(values, batches) if batch]
    if len(paired) < 2:
        return 0.0, 0
    grouped: dict[str, list[float]] = {}
    for value, batch in paired:
        grouped.setdefault(batch, []).append(value)
    if len(grouped) < 2:
        return 0.0, len(grouped)

    all_values = [value for values_per_batch in grouped.values() for value in values_per_batch]
    grand_mean = sum(all_values) / len(all_values)
    ss_total = sum((value - grand_mean) ** 2 for value in all_values)
    if ss_total == 0:
        return 0.0, len(grouped)
    ss_between = sum(len(vals) * ((sum(vals) / len(vals) - grand_mean) ** 2) for vals in grouped.values())
    return ss_between / ss_total, len(grouped)


def _build_phenotype_diagnostics(
    *,
    phenotype_path: Path,
    phenotype_format: str | None,
    trait_name: str,
    phenotype_headers: list[str],
) -> PhenotypeDiagnosticsSummary | None:
    if not phenotype_path.exists():
        return None
    rows = _iter_phenotype_rows(phenotype_path, phenotype_format)
    if not rows:
        return None

    batch_column = _pheno_batch_column()
    outlier_zscore_threshold = _pheno_outlier_zscore_threshold()
    high_outlier_ratio_threshold = _pheno_outlier_high_ratio_threshold()
    batch_effect_eta2_threshold = _pheno_batch_effect_eta2_threshold()

    trait_values, batch_values = _extract_trait_and_batch_values(rows, trait_name, batch_column)
    outlier_count = _compute_outlier_count(trait_values, outlier_zscore_threshold)
    outlier_ratio = (outlier_count / len(trait_values)) if trait_values else 0.0

    eta2, batch_level_count = _compute_batch_eta2(trait_values, batch_values)
    batch_effect_significant = eta2 >= batch_effect_eta2_threshold and batch_level_count >= 2

    recommendations: list[str] = []
    if outlier_ratio >= high_outlier_ratio_threshold and trait_values:
        recommendations.append("recommend robust outlier handling before model fitting")
    if batch_effect_significant:
        recommendations.append(f"recommend covariate={batch_column} or stratified validation split")

    return PhenotypeDiagnosticsSummary(
        sample_count=len(rows),
        trait_value_count=len(trait_values),
        outlier_count=outlier_count,
        outlier_ratio=outlier_ratio,
        outlier_zscore_threshold=outlier_zscore_threshold,
        high_outlier_ratio_threshold=high_outlier_ratio_threshold,
        batch_column=batch_column if batch_column in {h.strip() for h in phenotype_headers} else None,
        batch_level_count=batch_level_count,
        batch_effect_eta2=eta2,
        batch_effect_significant=batch_effect_significant,
        batch_effect_eta2_threshold=batch_effect_eta2_threshold,
        recommendations=recommendations,
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

    population_structure = _build_population_structure_summary()
    phenotype_diagnostics = _build_phenotype_diagnostics(
        phenotype_path=phenotype_path,
        phenotype_format=phenotype_format,
        trait_name=payload.trait_name,
        phenotype_headers=phenotype_headers,
    )
    risk_tags: list[str] = []
    if qc_risk_level == "high":
        risk_tags.append("qc_missingness_high")
    if population_structure is not None:
        if population_structure.outlier_samples:
            risk_tags.append("population_structure_outliers")
        if population_structure.high_relatedness_pair_count > 0:
            risk_tags.append("population_relatedness_high")
    if phenotype_diagnostics is not None:
        if phenotype_diagnostics.outlier_ratio >= phenotype_diagnostics.high_outlier_ratio_threshold:
            risk_tags.append("phenotype_outlier_high")
        if phenotype_diagnostics.batch_effect_significant:
            risk_tags.append("phenotype_batch_effect_significant")

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
        population_structure=population_structure,
        phenotype_diagnostics=phenotype_diagnostics,
        risk_tags=risk_tags,
        validation_flags=validation_flags,
    )
