"""Governance controls: scope authorization, quota checks, and observability audit."""

from __future__ import annotations

from animal_gs_agent.schemas.governance import GovernanceAuditResponse
from animal_gs_agent.schemas.jobs import JobStatusResponse


def is_scope_authorized(*, project_scope: str, access_scopes: list[str]) -> bool:
    normalized = {scope.strip() for scope in access_scopes if scope.strip()}
    return project_scope.strip() in normalized


def count_active_jobs_in_scope(*, project_scope: str, jobs: list[JobStatusResponse]) -> int:
    return sum(
        1
        for job in jobs
        if job.project_scope == project_scope and job.status in {"queued", "running"}
    )


def quota_allows_new_job(*, project_scope: str, quota_max_active: int, jobs: list[JobStatusResponse]) -> bool:
    if quota_max_active <= 0:
        return True
    return count_active_jobs_in_scope(project_scope=project_scope, jobs=jobs) < quota_max_active


def build_governance_audit(job: JobStatusResponse) -> GovernanceAuditResponse:
    latest_error_code = None
    failed_events = [item for item in job.events if item.error_code]
    if failed_events:
        latest_error_code = failed_events[-1].error_code
    escalation_seen = bool(
        job.escalation_resolution
        or job.escalation_requested_at
        or any(node.action.startswith("approve_escalation") for node in job.decision_trace)
    )
    return GovernanceAuditResponse(
        job_id=job.job_id,
        execution_status=job.status,
        project_scope=job.project_scope,
        requested_by=job.requested_by,
        event_count=len(job.events),
        decision_count=len(job.decision_trace),
        escalation_seen=escalation_seen,
        latest_error_code=latest_error_code,
    )
