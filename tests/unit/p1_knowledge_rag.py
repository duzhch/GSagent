import pytest

from animal_gs_agent.schemas.dataset_profile import (
    DatasetPathChecks,
    DatasetProfile,
    PhenotypeDiagnosticsSummary,
)
from animal_gs_agent.schemas.jobs import JobStatusResponse, RankedCandidate, WorkflowSummary
from animal_gs_agent.schemas.knowledge import KnowledgeDocument
from animal_gs_agent.schemas.task_understanding import TaskUnderstandingResult
from animal_gs_agent.services.knowledge_service import (
    build_knowledge_documents,
    build_recommendation_citations,
    retrieve_knowledge_evidence,
)


def _task() -> TaskUnderstandingResult:
    return TaskUnderstandingResult(
        request_scope="supported_gs",
        trait_name="daily_gain",
        user_goal="rank candidates",
        candidate_fixed_effects=["batch"],
        population_description="pig",
        missing_inputs=[],
        confidence=0.9,
        clarification_needed=False,
    )


def _profile_with_recommendation() -> DatasetProfile:
    return DatasetProfile(
        phenotype_path="/tmp/pheno.csv",
        genotype_path="/tmp/geno.vcf",
        path_checks=DatasetPathChecks(phenotype_exists=True, genotype_exists=True),
        phenotype_format="csv",
        genotype_format="vcf",
        phenotype_headers=["animal_id", "daily_gain", "batch"],
        trait_column_present=True,
        phenotype_diagnostics=PhenotypeDiagnosticsSummary(
            sample_count=4,
            trait_value_count=4,
            outlier_count=0,
            outlier_ratio=0.0,
            outlier_zscore_threshold=3.0,
            high_outlier_ratio_threshold=0.1,
            batch_column="batch",
            batch_level_count=2,
            batch_effect_eta2=0.45,
            batch_effect_significant=True,
            batch_effect_eta2_threshold=0.2,
            recommendations=["covariate=batch"],
        ),
        validation_flags=[],
    )


def _completed_job() -> JobStatusResponse:
    return JobStatusResponse(
        job_id="job-knowledge",
        status="completed",
        trait_name="daily_gain",
        task_understanding=_task(),
        dataset_profile=_profile_with_recommendation(),
        workflow_backend="native_nextflow",
        workflow_result_dir="/tmp/job-knowledge",
        workflow_summary=WorkflowSummary(
            trait_name="daily_gain",
            total_candidates=2,
            top_candidates=[
                RankedCandidate(individual_id="A1", gebv=1.20, rank=1),
                RankedCandidate(individual_id="A2", gebv=1.10, rank=2),
            ],
            model_metrics={"h2": "0.40"},
            source_files=["gblup/gebv_predictions.csv"],
        ),
    )


def test_knowledge_connector_loads_history_sop_and_literature(tmp_path) -> None:
    sop_path = tmp_path / "sop.md"
    sop_path.write_text("SOP: Use covariate=batch when batch effect is significant.", encoding="utf-8")
    literature_path = tmp_path / "paper.txt"
    literature_path.write_text("Literature: batch covariates improve stability in GS.", encoding="utf-8")

    docs = build_knowledge_documents(
        history_jobs=[_completed_job()],
        sop_paths=[str(sop_path)],
        literature_paths=[str(literature_path)],
    )

    source_types = {doc.source_type for doc in docs}
    assert "historical_task" in source_types
    assert "sop" in source_types
    assert "literature" in source_types


def test_retrieval_rerank_prefers_more_relevant_documents() -> None:
    docs = [
        KnowledgeDocument(
            source_id="sop-1",
            source_type="sop",
            title="Batch SOP",
            content="Use covariate=batch strategy for strong batch effects.",
        ),
        KnowledgeDocument(
            source_id="paper-1",
            source_type="literature",
            title="General GS",
            content="This text is about unrelated marker density.",
        ),
    ]

    ranked = retrieve_knowledge_evidence(
        query="batch covariate strategy",
        documents=docs,
        top_k=2,
    )

    assert ranked[0].source_id == "sop-1"
    assert ranked[0].score >= ranked[1].score
    assert "covariate" in ranked[0].snippet.lower()


def test_citation_conflict_is_marked_and_missing_evidence_is_rejected() -> None:
    docs = [
        KnowledgeDocument(
            source_id="lit-pos",
            source_type="literature",
            title="Positive",
            content="Covariate=batch is recommended for significant batch effect.",
        ),
        KnowledgeDocument(
            source_id="lit-neg",
            source_type="literature",
            title="Negative",
            content="Covariate=batch is not recommended when confounded with family.",
        ),
    ]

    citations = build_recommendation_citations(
        recommendations=["covariate=batch"],
        documents=docs,
        top_k_per_recommendation=2,
    )
    assert len(citations) == 1
    assert len(citations[0].evidence) >= 1
    assert citations[0].conflict is True
    assert citations[0].conflict_note is not None

    with pytest.raises(ValueError):
        build_recommendation_citations(
            recommendations=["covariate=batch"],
            documents=[],
            top_k_per_recommendation=1,
        )
