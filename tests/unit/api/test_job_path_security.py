import pytest
from fastapi import HTTPException

from animal_gs_agent.api.routes.jobs import _normalize_and_validate_paths
from animal_gs_agent.schemas.jobs import JobSubmissionRequest


def _payload(*, phenotype_path: str, genotype_path: str) -> JobSubmissionRequest:
    return JobSubmissionRequest(
        user_message="Run genomic selection for daily_gain",
        trait_name="daily_gain",
        phenotype_path=phenotype_path,
        genotype_path=genotype_path,
    )


def test_normalize_and_validate_paths_rejects_outside_allowed_roots(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ANIMAL_GS_AGENT_WORKDIR", str(tmp_path))
    monkeypatch.setenv("ANIMAL_GS_AGENT_ALLOWED_DATA_ROOTS", str(tmp_path / "allowed"))

    with pytest.raises(HTTPException) as exc_info:
        _normalize_and_validate_paths(
            _payload(
                phenotype_path="/etc/passwd",
                genotype_path="/etc/hosts",
            )
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "data_path_outside_allowed_roots"


def test_normalize_and_validate_paths_resolves_relative_paths(monkeypatch, tmp_path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    phenotype = data_dir / "pheno.csv"
    genotype = data_dir / "geno.vcf"
    phenotype.write_text("animal_id,daily_gain\nA1,1.0\n", encoding="utf-8")
    genotype.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")

    monkeypatch.setenv("ANIMAL_GS_AGENT_WORKDIR", str(tmp_path))
    monkeypatch.setenv("ANIMAL_GS_AGENT_ALLOWED_DATA_ROOTS", str(data_dir))

    normalized = _normalize_and_validate_paths(
        _payload(
            phenotype_path="data/pheno.csv",
            genotype_path="data/geno.vcf",
        )
    )

    assert normalized.phenotype_path == str(phenotype.resolve())
    assert normalized.genotype_path == str(genotype.resolve())
