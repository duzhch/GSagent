"""Audit services for claim-evidence validation."""

from typing import Literal

from animal_gs_agent.schemas.audit_claim import AuditCheckResult, ClaimEvidenceItem
from animal_gs_agent.schemas.jobs import JobStatusResponse


def _status_from_links(links: list[str]) -> Literal["accepted", "reject"]:
    return "accepted" if links else "reject"


def build_claim_evidence_map(job: JobStatusResponse) -> list[ClaimEvidenceItem]:
    source_files = job.workflow_summary.source_files if job.workflow_summary is not None else []
    workflow_evidence = [f"artifact:{path}" for path in source_files]

    intake_links: list[str] = []
    for node in job.decision_trace:
        if node.decision_id == "intake_accept_job":
            intake_links.append(f"trace:{node.decision_id}")
            break

    candidate_links: list[str] = []
    if any(path.endswith("gebv_predictions.csv") for path in source_files):
        candidate_links.append("artifact:gblup/gebv_predictions.csv")

    claims = [
        ClaimEvidenceItem(
            claim_id="dataset_validated_before_execution",
            claim_text="dataset contract was validated before workflow execution",
            evidence_links=intake_links,
            status=_status_from_links(intake_links),
        ),
        ClaimEvidenceItem(
            claim_id="workflow_execution_completed",
            claim_text="workflow execution completed and produced parseable outputs",
            evidence_links=workflow_evidence,
            status=_status_from_links(workflow_evidence),
        ),
        ClaimEvidenceItem(
            claim_id="top_candidates_reported",
            claim_text="top candidate ranking is grounded on workflow output files",
            evidence_links=candidate_links,
            status=_status_from_links(candidate_links),
        ),
    ]
    return claims


def _parse_metric(metrics: dict[str, str], key: str) -> float | None:
    raw = metrics.get(key)
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def run_audit_checks(job: JobStatusResponse) -> list[AuditCheckResult]:
    leakage_evidence: list[str] = []
    for node in job.decision_trace:
        for ev in node.evidence:
            if "leakage_overlap_detected" in ev:
                leakage_evidence.append(f"trace:{node.decision_id}")

    leakage_status: Literal["pass", "risk"] = "risk" if leakage_evidence else "pass"
    leakage_message = (
        "potential leakage evidence found in decision trace"
        if leakage_evidence
        else "no leakage overlap evidence detected"
    )

    metric_evidence: list[str] = []
    metric_status: Literal["pass", "risk"] = "pass"
    metric_message = "metric ranges are consistent"

    if job.workflow_summary is not None:
        metrics = job.workflow_summary.model_metrics
        pearson = _parse_metric(metrics, "metric::pearson")
        rmse = _parse_metric(metrics, "metric::rmse")
        if pearson is not None and (pearson < -1.0 or pearson > 1.0):
            metric_evidence.append(f"metric::pearson={pearson}")
        if rmse is not None and rmse < 0.0:
            metric_evidence.append(f"metric::rmse={rmse}")

    if metric_evidence:
        metric_status = "risk"
        metric_message = "metric value out of expected range"

    return [
        AuditCheckResult(
            check_id="leakage_check",
            status=leakage_status,
            evidence_links=leakage_evidence,
            message=leakage_message,
        ),
        AuditCheckResult(
            check_id="metric_consistency_check",
            status=metric_status,
            evidence_links=metric_evidence,
            message=metric_message,
        ),
    ]
