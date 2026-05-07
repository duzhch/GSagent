from animal_gs_agent.schemas.jobs import JobSubmissionRequest
from animal_gs_agent.services.dataset_profile_service import build_dataset_profile


def test_build_dataset_profile_extracts_headers_and_trait_presence(tmp_path) -> None:
    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text("animal_id,daily_gain,sex\nA1,1.2,M\n", encoding="utf-8")

    genotype_file = tmp_path / "geno.pgen"
    genotype_file.write_text("placeholder", encoding="utf-8")

    payload = JobSubmissionRequest(
        user_message="Run genomic selection for daily_gain",
        trait_name="daily_gain",
        phenotype_path=str(phenotype_file),
        genotype_path=str(genotype_file),
    )

    profile = build_dataset_profile(payload)

    assert profile.phenotype_format == "csv"
    assert profile.genotype_format == "pgen"
    assert profile.phenotype_headers == ["animal_id", "daily_gain", "sex"]
    assert profile.trait_column_present is True


def test_build_dataset_profile_marks_missing_trait_column(tmp_path) -> None:
    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text("animal_id,sex\nA1,M\n", encoding="utf-8")

    genotype_file = tmp_path / "geno.pgen"
    genotype_file.write_text("placeholder", encoding="utf-8")

    payload = JobSubmissionRequest(
        user_message="Run genomic selection for daily_gain",
        trait_name="daily_gain",
        phenotype_path=str(phenotype_file),
        genotype_path=str(genotype_file),
    )

    profile = build_dataset_profile(payload)

    assert profile.trait_column_present is False
    assert "trait_column_missing" in profile.validation_flags
