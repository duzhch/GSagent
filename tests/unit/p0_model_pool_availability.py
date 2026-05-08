from animal_gs_agent.schemas.dataset_profile import (
    DatasetPathChecks,
    DatasetProfile,
    PhenotypeDiagnosticsSummary,
)
from animal_gs_agent.schemas.task_understanding import TaskUnderstandingResult
from animal_gs_agent.services.model_pool_service import build_model_pool_plan


def _task() -> TaskUnderstandingResult:
    return TaskUnderstandingResult(
        request_scope="supported_gs",
        trait_name="daily_gain",
        user_goal="rank candidates",
        candidate_fixed_effects=["sex", "batch"],
        population_description="pig",
        missing_inputs=[],
        confidence=0.9,
        clarification_needed=False,
    )


def test_model_pool_marks_models_available_on_clean_profile() -> None:
    profile = DatasetProfile(
        phenotype_path="/tmp/pheno.csv",
        genotype_path="/tmp/geno.vcf",
        path_checks=DatasetPathChecks(phenotype_exists=True, genotype_exists=True),
        phenotype_format="csv",
        genotype_format="vcf",
        phenotype_headers=["animal_id", "daily_gain"],
        trait_column_present=True,
        validation_flags=[],
        risk_tags=[],
        phenotype_diagnostics=PhenotypeDiagnosticsSummary(
            sample_count=300,
            trait_value_count=300,
            outlier_count=0,
            outlier_ratio=0.0,
            outlier_zscore_threshold=3.0,
            high_outlier_ratio_threshold=0.1,
            batch_column="batch",
            batch_level_count=2,
            batch_effect_eta2=0.05,
            batch_effect_significant=False,
            batch_effect_eta2_threshold=0.2,
            recommendations=[],
        ),
    )

    pool = build_model_pool_plan(_task(), profile)
    by_model = {item.model_id: item for item in pool.candidates}

    assert pool.available_models == ["GBLUP", "BayesB", "XGBoost"]
    assert by_model["GBLUP"].available is True
    assert by_model["BayesB"].available is True
    assert by_model["XGBoost"].available is True


def test_model_pool_returns_disable_reasons_for_unmet_conditions() -> None:
    profile = DatasetProfile(
        phenotype_path="/tmp/pheno.csv",
        genotype_path="/tmp/geno.vcf",
        path_checks=DatasetPathChecks(phenotype_exists=True, genotype_exists=True),
        phenotype_format="csv",
        genotype_format="vcf",
        phenotype_headers=["animal_id"],
        trait_column_present=False,
        validation_flags=["trait_column_missing", "qc_risk_high"],
        risk_tags=["phenotype_batch_effect_significant"],
        phenotype_diagnostics=PhenotypeDiagnosticsSummary(
            sample_count=20,
            trait_value_count=20,
            outlier_count=3,
            outlier_ratio=0.15,
            outlier_zscore_threshold=3.0,
            high_outlier_ratio_threshold=0.1,
            batch_column="batch",
            batch_level_count=2,
            batch_effect_eta2=0.4,
            batch_effect_significant=True,
            batch_effect_eta2_threshold=0.2,
            recommendations=["recommend covariate=batch"],
        ),
    )

    pool = build_model_pool_plan(_task(), profile)
    by_model = {item.model_id: item for item in pool.candidates}

    assert by_model["GBLUP"].available is False
    assert "trait_column_missing" in by_model["GBLUP"].disabled_reasons

    assert by_model["BayesB"].available is False
    assert "insufficient_trait_records_for_bayesb" in by_model["BayesB"].disabled_reasons

    assert by_model["XGBoost"].available is False
    assert "qc_risk_high" in by_model["XGBoost"].disabled_reasons
