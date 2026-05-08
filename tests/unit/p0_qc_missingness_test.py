from animal_gs_agent.schemas.jobs import JobSubmissionRequest
from animal_gs_agent.services.dataset_profile_service import build_dataset_profile


def test_p0_qc_missingness_outputs_sample_and_variant_stats(monkeypatch, tmp_path) -> None:
    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text("animal_id,daily_gain\nA1,1.2\n", encoding="utf-8")
    genotype_file = tmp_path / "geno.bed"
    genotype_file.write_text("placeholder", encoding="utf-8")

    smiss = tmp_path / "plink.smiss"
    smiss.write_text(
        "\n".join(
            [
                "FID IID MISS_PHENO N_MISS N_GENO F_MISS",
                "A1 A1 0 1 100 0.010",
                "A2 A2 0 5 100 0.050",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    vmiss = tmp_path / "plink.vmiss"
    vmiss.write_text(
        "\n".join(
            [
                "CHROM ID POS N_MISS N_GENO F_MISS",
                "1 rs1 100 10 1000 0.010",
                "1 rs2 200 20 1000 0.020",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("ANIMAL_GS_AGENT_PLINK2_SMISS_PATH", str(smiss))
    monkeypatch.setenv("ANIMAL_GS_AGENT_PLINK2_VMISS_PATH", str(vmiss))
    monkeypatch.setenv("ANIMAL_GS_AGENT_QC_MISSINGNESS_HIGH_THRESHOLD", "0.10")

    profile = build_dataset_profile(
        JobSubmissionRequest(
            user_message="run gs",
            trait_name="daily_gain",
            phenotype_path=str(phenotype_file),
            genotype_path=str(genotype_file),
        )
    )

    assert profile.genotype_missingness is not None
    assert profile.genotype_missingness.sample_count == 2
    assert profile.genotype_missingness.variant_count == 2


def test_p0_qc_missingness_sets_high_risk_flag(monkeypatch, tmp_path) -> None:
    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text("animal_id,daily_gain\nA1,1.2\n", encoding="utf-8")
    genotype_file = tmp_path / "geno.bed"
    genotype_file.write_text("placeholder", encoding="utf-8")

    smiss = tmp_path / "plink.smiss"
    smiss.write_text(
        "\n".join(
            [
                "FID IID MISS_PHENO N_MISS N_GENO F_MISS",
                "A1 A1 0 20 100 0.200",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    vmiss = tmp_path / "plink.vmiss"
    vmiss.write_text(
        "\n".join(
            [
                "CHROM ID POS N_MISS N_GENO F_MISS",
                "1 rs1 100 10 1000 0.010",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ANIMAL_GS_AGENT_PLINK2_SMISS_PATH", str(smiss))
    monkeypatch.setenv("ANIMAL_GS_AGENT_PLINK2_VMISS_PATH", str(vmiss))
    monkeypatch.setenv("ANIMAL_GS_AGENT_QC_MISSINGNESS_HIGH_THRESHOLD", "0.10")

    profile = build_dataset_profile(
        JobSubmissionRequest(
            user_message="run gs",
            trait_name="daily_gain",
            phenotype_path=str(phenotype_file),
            genotype_path=str(genotype_file),
        )
    )

    assert profile.qc_risk_level == "high"
    assert "qc_risk_high" in profile.validation_flags
