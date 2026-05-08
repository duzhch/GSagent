from animal_gs_agent.schemas.dataset_profile import DatasetPathChecks, DatasetProfile
from animal_gs_agent.schemas.jobs import JobSubmissionRequest
from animal_gs_agent.schemas.task_understanding import TaskUnderstandingResult
from animal_gs_agent.services.job_service import create_job, jobs_store


def _request() -> JobSubmissionRequest:
    return JobSubmissionRequest(
        user_message="Run genomic selection for daily_gain",
        trait_name="daily_gain",
        phenotype_path="/tmp/pheno.csv",
        genotype_path="/tmp/geno.vcf",
    )


def _task() -> TaskUnderstandingResult:
    return TaskUnderstandingResult(
        request_scope="supported_gs",
        trait_name="daily_gain",
        user_goal="rank candidates",
        candidate_fixed_effects=["sex"],
        population_description="pig",
        missing_inputs=[],
        confidence=0.9,
        clarification_needed=False,
    )


def _profile() -> DatasetProfile:
    return DatasetProfile(
        phenotype_path="/tmp/pheno.csv",
        genotype_path="/tmp/geno.vcf",
        path_checks=DatasetPathChecks(phenotype_exists=True, genotype_exists=True),
        phenotype_format="csv",
        genotype_format="vcf",
        phenotype_headers=["animal_id", "daily_gain"],
        trait_column_present=True,
        validation_flags=[],
    )


def test_decision_trace_is_initialized_with_required_fields(monkeypatch) -> None:
    monkeypatch.delenv("ANIMAL_GS_AGENT_JOB_STORE_PATH", raising=False)
    monkeypatch.delenv("ANIMAL_GS_AGENT_JOB_STORE_SQLITE_PATH", raising=False)
    jobs_store.clear()

    created = create_job(_request(), task_understanding=_task(), dataset_profile=_profile())
    assert len(created.decision_trace) >= 1

    first = created.decision_trace[0]
    assert first.feature_id == "F-P0-01-02"
    assert first.agent_id == "supervisor"
    assert first.action == "accept_job"
    assert first.decision_id
    assert first.timestamp
    assert 0 <= first.confidence <= 1
    assert first.status in {"success", "failed", "running"}
    assert first.duration_ms is not None
