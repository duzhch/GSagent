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


def test_build_dataset_profile_accepts_gzipped_vcf(tmp_path) -> None:
    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text("animal_id,daily_gain\nA1,1.2\n", encoding="utf-8")

    genotype_file = tmp_path / "geno.vcf.gz"
    genotype_file.write_text("placeholder", encoding="utf-8")

    payload = JobSubmissionRequest(
        user_message="Run genomic selection for daily_gain",
        trait_name="daily_gain",
        phenotype_path=str(phenotype_file),
        genotype_path=str(genotype_file),
    )

    profile = build_dataset_profile(payload)

    assert profile.genotype_format == "vcf"
    assert "genotype_format_unsupported" not in profile.validation_flags


def test_build_dataset_profile_accepts_long_format_trait_value_headers(tmp_path) -> None:
    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text(
        "individual_id,trait,value,year\nA1,daily_gain,1.2,2023\n",
        encoding="utf-8",
    )

    genotype_file = tmp_path / "geno.vcf"
    genotype_file.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")

    payload = JobSubmissionRequest(
        user_message="Run genomic selection for daily_gain",
        trait_name="daily_gain",
        phenotype_path=str(phenotype_file),
        genotype_path=str(genotype_file),
    )

    profile = build_dataset_profile(payload)

    assert profile.trait_column_present is True
    assert "trait_column_missing" not in profile.validation_flags


def test_build_dataset_profile_parses_plink2_missingness_reports(monkeypatch, tmp_path) -> None:
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

    payload = JobSubmissionRequest(
        user_message="Run genomic selection for daily_gain",
        trait_name="daily_gain",
        phenotype_path=str(phenotype_file),
        genotype_path=str(genotype_file),
    )
    profile = build_dataset_profile(payload)

    assert profile.genotype_missingness is not None
    assert profile.genotype_missingness.sample_count == 2
    assert profile.genotype_missingness.variant_count == 2
    assert profile.genotype_missingness.sample_missing_rate_max == 0.05
    assert profile.genotype_missingness.variant_missing_rate_max == 0.02
    assert profile.qc_risk_level == "low"


def test_build_dataset_profile_marks_high_risk_when_missingness_exceeds_threshold(
    monkeypatch, tmp_path
) -> None:
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

    payload = JobSubmissionRequest(
        user_message="Run genomic selection for daily_gain",
        trait_name="daily_gain",
        phenotype_path=str(phenotype_file),
        genotype_path=str(genotype_file),
    )
    profile = build_dataset_profile(payload)

    assert profile.genotype_missingness is not None
    assert profile.qc_risk_level == "high"
    assert "qc_risk_high" in profile.validation_flags


def test_build_dataset_profile_parses_population_structure_and_outliers(monkeypatch, tmp_path) -> None:
    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text("animal_id,daily_gain\nA1,1.2\n", encoding="utf-8")
    genotype_file = tmp_path / "geno.vcf"
    genotype_file.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")

    eigenvec = tmp_path / "plink.eigenvec"
    eigenvec.write_text(
        "\n".join(
            [
                "#FID IID PC1 PC2",
                "F1 A1 0.10 0.10",
                "F1 A2 0.20 0.20",
                "F1 A3 5.00 5.00",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    relatedness = tmp_path / "plink.genome"
    relatedness.write_text(
        "\n".join(
            [
                "FID1 IID1 FID2 IID2 PI_HAT",
                "F1 A1 F1 A2 0.10",
                "F1 A2 F1 A3 0.35",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("ANIMAL_GS_AGENT_PLINK2_PCA_EIGENVEC_PATH", str(eigenvec))
    monkeypatch.setenv("ANIMAL_GS_AGENT_PLINK2_RELATEDNESS_PATH", str(relatedness))
    monkeypatch.setenv("ANIMAL_GS_AGENT_QC_PCA_ZSCORE_THRESHOLD", "1.0")
    monkeypatch.setenv("ANIMAL_GS_AGENT_QC_RELATEDNESS_HIGH_THRESHOLD", "0.25")

    payload = JobSubmissionRequest(
        user_message="Run genomic selection for daily_gain",
        trait_name="daily_gain",
        phenotype_path=str(phenotype_file),
        genotype_path=str(genotype_file),
    )
    profile = build_dataset_profile(payload)

    assert profile.population_structure is not None
    assert profile.population_structure.sample_count == 3
    assert "A3" in profile.population_structure.outlier_samples
    assert profile.population_structure.high_relatedness_pair_count == 1
    assert "population_structure_outliers" in profile.risk_tags
    assert "population_relatedness_high" in profile.risk_tags


def test_build_dataset_profile_handles_headerless_eigenvec(monkeypatch, tmp_path) -> None:
    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text("animal_id,daily_gain\nA1,1.2\n", encoding="utf-8")
    genotype_file = tmp_path / "geno.vcf"
    genotype_file.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")

    eigenvec = tmp_path / "plink.eigenvec"
    eigenvec.write_text(
        "\n".join(
            [
                "F1 A1 0.10 0.10",
                "F1 A2 0.20 0.20",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ANIMAL_GS_AGENT_PLINK2_PCA_EIGENVEC_PATH", str(eigenvec))

    payload = JobSubmissionRequest(
        user_message="Run genomic selection for daily_gain",
        trait_name="daily_gain",
        phenotype_path=str(phenotype_file),
        genotype_path=str(genotype_file),
    )
    profile = build_dataset_profile(payload)

    assert profile.population_structure is not None
    assert profile.population_structure.sample_count == 2
    assert profile.population_structure.pc_columns == ["PC1", "PC2"]


def test_build_dataset_profile_generates_phenotype_outlier_and_batch_diagnostics(
    monkeypatch, tmp_path
) -> None:
    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text(
        "\n".join(
            [
                "animal_id,daily_gain,batch",
                "A1,1.0,B1",
                "A2,1.1,B1",
                "A3,6.0,B2",
                "A4,6.2,B2",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    genotype_file = tmp_path / "geno.vcf"
    genotype_file.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")

    monkeypatch.setenv("ANIMAL_GS_AGENT_PHENO_BATCH_COLUMN", "batch")
    monkeypatch.setenv("ANIMAL_GS_AGENT_PHENO_OUTLIER_ZSCORE_THRESHOLD", "1.0")
    monkeypatch.setenv("ANIMAL_GS_AGENT_PHENO_OUTLIER_HIGH_RATIO_THRESHOLD", "0.10")
    monkeypatch.setenv("ANIMAL_GS_AGENT_PHENO_BATCH_EFFECT_MIN_ETA2", "0.20")

    payload = JobSubmissionRequest(
        user_message="Run genomic selection for daily_gain",
        trait_name="daily_gain",
        phenotype_path=str(phenotype_file),
        genotype_path=str(genotype_file),
    )
    profile = build_dataset_profile(payload)

    assert profile.phenotype_diagnostics is not None
    assert profile.phenotype_diagnostics.sample_count == 4
    assert profile.phenotype_diagnostics.outlier_ratio >= 0.25
    assert profile.phenotype_diagnostics.batch_effect_significant is True
    assert "phenotype_outlier_high" in profile.risk_tags
    assert "phenotype_batch_effect_significant" in profile.risk_tags
    assert any("covariate" in msg for msg in profile.phenotype_diagnostics.recommendations)


def test_build_dataset_profile_handles_missing_batch_column(monkeypatch, tmp_path) -> None:
    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text(
        "\n".join(
            [
                "animal_id,daily_gain",
                "A1,1.0",
                "A2,1.2",
                "A3,1.1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    genotype_file = tmp_path / "geno.vcf"
    genotype_file.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")
    monkeypatch.setenv("ANIMAL_GS_AGENT_PHENO_BATCH_COLUMN", "batch")

    payload = JobSubmissionRequest(
        user_message="Run genomic selection for daily_gain",
        trait_name="daily_gain",
        phenotype_path=str(phenotype_file),
        genotype_path=str(genotype_file),
    )
    profile = build_dataset_profile(payload)

    assert profile.phenotype_diagnostics is not None
    assert profile.phenotype_diagnostics.batch_effect_significant is False
    assert profile.phenotype_diagnostics.batch_level_count == 0
