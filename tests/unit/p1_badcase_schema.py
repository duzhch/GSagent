from animal_gs_agent.schemas.badcase import BadcaseRecord
from animal_gs_agent.services.badcase_service import (
    build_badcase_advice,
    build_badcase_record,
)
from animal_gs_agent.schemas.dataset_profile import (
    DatasetPathChecks,
    DatasetProfile,
    PhenotypeDiagnosticsSummary,
)
from animal_gs_agent.schemas.jobs import JobStatusResponse, RankedCandidate, WorkflowSummary
from animal_gs_agent.schemas.task_understanding import TaskUnderstandingResult


def _task() -> TaskUnderstandingResult:
    return TaskUnderstandingResult(
        request_scope="supported_gs",
        trait_name="daily_gain",
        user_goal="rank candidates",
        candidate_fixed_effects=["batch"],
        population_description="pig",
        missing_inputs=[],
        confidence=0.88,
        clarification_needed=False,
    )


def _profile(risk_tags: list[str], recommendations: list[str]) -> DatasetProfile:
    return DatasetProfile(
        phenotype_path="/tmp/pheno.csv",
        genotype_path="/tmp/geno.vcf",
        path_checks=DatasetPathChecks(phenotype_exists=True, genotype_exists=True),
        phenotype_format="csv",
        genotype_format="vcf",
        phenotype_headers=["animal_id", "daily_gain", "batch"],
        trait_column_present=True,
        risk_tags=risk_tags,
        phenotype_diagnostics=PhenotypeDiagnosticsSummary(
            sample_count=8,
            trait_value_count=8,
            outlier_count=1,
            outlier_ratio=0.125,
            outlier_zscore_threshold=3.0,
            high_outlier_ratio_threshold=0.1,
            batch_column="batch",
            batch_level_count=2,
            batch_effect_eta2=0.41,
            batch_effect_significant=True,
            batch_effect_eta2_threshold=0.2,
            recommendations=recommendations,
        ),
        validation_flags=[],
    )


def _historical_job() -> JobStatusResponse:
    return JobStatusResponse(
        job_id="hist-001",
        status="completed",
        trait_name="daily_gain",
        task_understanding=_task(),
        dataset_profile=_profile(
            risk_tags=["population_structure_outliers"],
            recommendations=["covariate=batch"],
        ),
        workflow_summary=WorkflowSummary(
            trait_name="daily_gain",
            total_candidates=2,
            top_candidates=[
                RankedCandidate(individual_id="A1", gebv=1.2, rank=1),
                RankedCandidate(individual_id="A2", gebv=1.1, rank=2),
            ],
            model_metrics={"h2": "0.4"},
            source_files=["gblup/gebv_predictions.csv"],
        ),
    )


def test_badcase_record_schema_from_job() -> None:
    record = build_badcase_record(_historical_job())

    assert isinstance(record, BadcaseRecord)
    assert record.job_id == "hist-001"
    assert record.trait_name == "daily_gain"
    assert "population_structure_outliers" in record.risk_tags
    assert "covariate=batch" in record.recommendations


def test_badcase_similarity_returns_preventive_actions_when_high_similarity() -> None:
    advice = build_badcase_advice(
        task_understanding=_task(),
        dataset_profile=_profile(risk_tags=[], recommendations=[]),
        historical_jobs=[_historical_job()],
        similarity_threshold=0.40,
        top_k=3,
    )

    assert advice.queried is True
    assert advice.high_similarity_hit is True
    assert len(advice.similar_cases) >= 1
    assert advice.similar_cases[0].similarity >= 0.40
    assert any("covariate=batch" in action for action in advice.preventive_actions)
