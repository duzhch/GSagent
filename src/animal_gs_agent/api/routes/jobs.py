"""Job submission routes."""

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from animal_gs_agent.agent.task_understanding import (
    TaskUnderstandingProviderError,
    TaskUnderstandingValidationError,
    understand_task,
)
from animal_gs_agent.config import get_settings
from animal_gs_agent.llm.client import OpenAICompatibleLLMClient
from animal_gs_agent.schemas.jobs import (
    JobArtifactsResponse,
    JobDecisionTraceResponse,
    JobEscalationResolutionRequest,
    JobQCOverrideRequest,
    JobReportResponse,
    JobStatusResponse,
    JobSubmissionRequest,
    JobSubmissionResponse,
)
from animal_gs_agent.schemas.governance import GovernanceAuditResponse
from animal_gs_agent.services.artifact_service import list_artifacts
from animal_gs_agent.services.dataset_profile_service import build_dataset_profile
from animal_gs_agent.services.governance_service import build_governance_audit
from animal_gs_agent.services.job_service import (
    create_job,
    get_job,
    mark_job_queued_for_worker,
    resolve_job_escalation_abort,
    resolve_job_escalation_retry,
    resolve_qc_block_override,
    refresh_running_job,
    run_job,
)
from animal_gs_agent.services.report_service import build_job_report
from animal_gs_agent.services.run_queue_service import enqueue_run_job
from animal_gs_agent.services.slurm_service import poll_slurm_job_state
from animal_gs_agent.services.workflow_result_service import parse_workflow_outputs
from animal_gs_agent.services.workflow_service import execute_fixed_workflow


def _runtime_workdir() -> Path:
    return Path(os.getenv("ANIMAL_GS_AGENT_WORKDIR", os.getcwd())).expanduser().resolve()


def _allowed_data_roots() -> list[Path]:
    configured = os.getenv("ANIMAL_GS_AGENT_ALLOWED_DATA_ROOTS", "").strip()
    if not configured:
        return [_runtime_workdir()]

    roots: list[Path] = []
    for item in configured.split(","):
        token = item.strip()
        if token:
            roots.append(Path(token).expanduser().resolve())
    return roots or [_runtime_workdir()]


def _resolve_user_path(raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = _runtime_workdir() / candidate
    return candidate.resolve()


def _within_root(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _normalize_and_validate_paths(payload: JobSubmissionRequest) -> JobSubmissionRequest:
    phenotype = _resolve_user_path(payload.phenotype_path)
    genotype = _resolve_user_path(payload.genotype_path)
    allowed_roots = _allowed_data_roots()
    if not any(_within_root(phenotype, root) for root in allowed_roots):
        raise HTTPException(status_code=403, detail="data_path_outside_allowed_roots")
    if not any(_within_root(genotype, root) for root in allowed_roots):
        raise HTTPException(status_code=403, detail="data_path_outside_allowed_roots")
    return payload.model_copy(
        update={
            "phenotype_path": str(phenotype),
            "genotype_path": str(genotype),
        }
    )


def create_jobs_router() -> APIRouter:
    router = APIRouter()

    @router.post(
        "/jobs",
        response_model=JobSubmissionResponse,
        response_model_exclude_none=True,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def submit_job(payload: JobSubmissionRequest) -> JobSubmissionResponse:
        payload = _normalize_and_validate_paths(payload)
        settings = get_settings()
        if not settings.llm.base_url or not settings.llm.api_key or not settings.llm.model:
            raise HTTPException(status_code=503, detail="LLM provider is not configured")

        client = OpenAICompatibleLLMClient(settings.llm)
        try:
            task_understanding = understand_task(payload.user_message, llm_client=client)
        except (TaskUnderstandingProviderError, TaskUnderstandingValidationError) as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        dataset_profile = build_dataset_profile(payload)
        try:
            return create_job(
                payload,
                task_understanding=task_understanding,
                dataset_profile=dataset_profile,
            )
        except ValueError as exc:
            detail = str(exc)
            if detail == "authz_scope_denied":
                raise HTTPException(status_code=403, detail=detail) from exc
            if detail == "project_quota_exceeded":
                raise HTTPException(status_code=429, detail=detail) from exc
            raise HTTPException(status_code=409, detail=detail) from exc

    @router.get("/jobs/{job_id}", response_model=JobStatusResponse, response_model_exclude_none=True)
    def get_job_status(job_id: str) -> JobStatusResponse:
        job = refresh_running_job(
            job_id,
            slurm_state_checker=poll_slurm_job_state,
            workflow_output_parser=parse_workflow_outputs,
        )
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        return job

    @router.get("/jobs/{job_id}/trace", response_model=JobDecisionTraceResponse)
    def get_job_trace(job_id: str) -> JobDecisionTraceResponse:
        job = get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        return JobDecisionTraceResponse(
            job_id=job.job_id,
            status=job.status,
            decision_trace=job.decision_trace,
        )

    @router.post("/jobs/{job_id}/run", response_model=JobStatusResponse, response_model_exclude_none=True)
    def run_submitted_job(job_id: str) -> JobStatusResponse:
        async_enabled = os.getenv("ANIMAL_GS_AGENT_ASYNC_RUN_ENABLED", "").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        if async_enabled:
            job = mark_job_queued_for_worker(job_id)
            if job is None:
                raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
            enqueue_run_job(job_id)
            return job

        job = run_job(
            job_id,
            workflow_executor=execute_fixed_workflow,
            workflow_output_parser=parse_workflow_outputs,
        )
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        return job

    @router.post(
        "/jobs/{job_id}/escalation/retry",
        response_model=JobStatusResponse,
        response_model_exclude_none=True,
    )
    def retry_escalated_job(job_id: str, payload: JobEscalationResolutionRequest) -> JobStatusResponse:
        try:
            job = resolve_job_escalation_retry(job_id, approver=payload.approver, reason=payload.reason)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        async_enabled = os.getenv("ANIMAL_GS_AGENT_ASYNC_RUN_ENABLED", "").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        if async_enabled:
            enqueue_run_job(job_id)
        return job

    @router.post(
        "/jobs/{job_id}/escalation/abort",
        response_model=JobStatusResponse,
        response_model_exclude_none=True,
    )
    def abort_escalated_job(job_id: str, payload: JobEscalationResolutionRequest) -> JobStatusResponse:
        try:
            job = resolve_job_escalation_abort(job_id, approver=payload.approver, reason=payload.reason)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        return job

    @router.post(
        "/jobs/{job_id}/qc/override",
        response_model=JobStatusResponse,
        response_model_exclude_none=True,
    )
    def override_qc_block(job_id: str, payload: JobQCOverrideRequest) -> JobStatusResponse:
        try:
            job = resolve_qc_block_override(job_id, approver=payload.approver, reason=payload.reason)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        return job

    @router.get("/jobs/{job_id}/report", response_model=JobReportResponse)
    def get_job_report(job_id: str) -> JobReportResponse:
        job = get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        if job.status != "completed":
            raise HTTPException(status_code=409, detail=f"Job {job_id} is not completed")
        try:
            return build_job_report(job)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.get("/jobs/{job_id}/artifacts", response_model=JobArtifactsResponse)
    def get_job_artifacts(job_id: str) -> JobArtifactsResponse:
        job = get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        if job.status != "completed":
            raise HTTPException(status_code=409, detail=f"Job {job_id} is not completed")
        if not job.workflow_result_dir:
            raise HTTPException(status_code=409, detail=f"Job {job_id} has no workflow result directory")
        try:
            artifacts = list_artifacts(job.workflow_result_dir)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return JobArtifactsResponse(
            job_id=job_id,
            status=job.status,
            artifact_count=len(artifacts),
            artifacts=artifacts,
        )

    @router.get("/jobs/{job_id}/governance/audit", response_model=GovernanceAuditResponse)
    def get_job_governance_audit(job_id: str) -> GovernanceAuditResponse:
        job = get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        return build_governance_audit(job)

    return router
