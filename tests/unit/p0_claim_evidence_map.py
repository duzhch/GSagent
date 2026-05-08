from animal_gs_agent.schemas.dataset_profile import DatasetPathChecks, DatasetProfile
from animal_gs_agent.schemas.jobs import (
    JobStatusResponse,
    JobSubmissionRequest,
    RankedCandidate,
    WorkflowSummary,
)
from animal_gs_agent.schemas.task_understanding import TaskUnderstandingResult
from animal_gs_agent.services.audit_service import build_claim_evidence_map
from animal_gs_agent.services.job_service import create_job, jobs_store
from animal_gs_agent.services.report_service import build_job_report
from animal_gs_agent.services.audit_service import run_audit_checks


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


def _completed_job() -> JobStatusResponse:
    created = create_job(_request(), task_understanding=_task(), dataset_profile=_profile())
    completed = JobStatusResponse.model_validate(
        {
            **created.model_dump(),
            "status": "completed",
            "workflow_backend": "native_nextflow",
            "workflow_result_dir": "/tmp/run-job001",
            "workflow_summary": WorkflowSummary(
                trait_name="daily_gain",
                total_candidates=2,
                top_candidates=[
                    RankedCandidate(individual_id="A1", gebv=1.2, rank=1),
                    RankedCandidate(individual_id="A2", gebv=1.1, rank=2),
                ],
                model_metrics={"h2": "0.42"},
                source_files=["gblup/gebv_predictions.csv", "gblup/model_summary.txt"],
            ).model_dump(),
        }
    )
    return completed


def test_claim_evidence_map_binds_evidence_links_for_each_claim(monkeypatch) -> None:
    monkeypatch.delenv("ANIMAL_GS_AGENT_JOB_STORE_PATH", raising=False)
    monkeypatch.delenv("ANIMAL_GS_AGENT_JOB_STORE_SQLITE_PATH", raising=False)
    jobs_store.clear()

    claims = build_claim_evidence_map(_completed_job())

    assert len(claims) >= 3
    assert all(item.evidence_links for item in claims)
    assert all(item.status == "accepted" for item in claims)
    workflow_claim = [item for item in claims if item.claim_id == "workflow_execution_completed"][0]
    assert "artifact:gblup/gebv_predictions.csv" in workflow_claim.evidence_links


def test_job_report_exposes_claim_evidence_map(monkeypatch) -> None:
    monkeypatch.delenv("ANIMAL_GS_AGENT_JOB_STORE_PATH", raising=False)
    monkeypatch.delenv("ANIMAL_GS_AGENT_JOB_STORE_SQLITE_PATH", raising=False)
    jobs_store.clear()

    report = build_job_report(_completed_job())

    assert report.claim_evidence_map
    assert len(report.claim_evidence_map) >= 3
    assert all(item.evidence_links for item in report.claim_evidence_map)


def test_claim_without_evidence_is_rejected(monkeypatch) -> None:
    monkeypatch.delenv("ANIMAL_GS_AGENT_JOB_STORE_PATH", raising=False)
    monkeypatch.delenv("ANIMAL_GS_AGENT_JOB_STORE_SQLITE_PATH", raising=False)
    jobs_store.clear()

    created = create_job(_request(), task_understanding=_task(), dataset_profile=_profile())
    completed = JobStatusResponse.model_validate(
        {
            **created.model_dump(),
            "status": "completed",
            "workflow_backend": "native_nextflow",
            "workflow_result_dir": "/tmp/run-job002",
            "workflow_summary": WorkflowSummary(
                trait_name="daily_gain",
                total_candidates=0,
                top_candidates=[],
                model_metrics={},
                source_files=[],
            ).model_dump(),
            "decision_trace": [],
        }
    )

    claims = build_claim_evidence_map(completed)
    by_claim = {item.claim_id: item for item in claims}

    assert by_claim["dataset_validated_before_execution"].status == "reject"
    assert by_claim["workflow_execution_completed"].status == "reject"
    assert by_claim["top_candidates_reported"].status == "reject"


def test_audit_checks_detect_leakage_and_metric_conflict(monkeypatch) -> None:
    monkeypatch.delenv("ANIMAL_GS_AGENT_JOB_STORE_PATH", raising=False)
    monkeypatch.delenv("ANIMAL_GS_AGENT_JOB_STORE_SQLITE_PATH", raising=False)
    jobs_store.clear()

    created = create_job(_request(), task_understanding=_task(), dataset_profile=_profile())
    checked = JobStatusResponse.model_validate(
        {
            **created.model_dump(),
            "status": "completed",
            "workflow_backend": "native_nextflow",
            "workflow_summary": WorkflowSummary(
                trait_name="daily_gain",
                total_candidates=2,
                top_candidates=[
                    RankedCandidate(individual_id="A1", gebv=1.2, rank=1),
                    RankedCandidate(individual_id="A2", gebv=1.1, rank=2),
                ],
                model_metrics={
                    "metric::pearson": "1.20",
                    "metric::rmse": "-0.10",
                },
                source_files=["gblup/gebv_predictions.csv"],
            ).model_dump(),
            "decision_trace": [
                *created.decision_trace,
                {
                    **created.decision_trace[0].model_dump(),
                    "decision_id": "audit_probe",
                    "action": "probe",
                    "evidence": ["leakage_overlap_detected"],
                },
            ],
        }
    )

    verdicts = run_audit_checks(checked)
    by_check = {item.check_id: item for item in verdicts}

    assert by_check["leakage_check"].status == "risk"
    assert by_check["metric_consistency_check"].status == "risk"
