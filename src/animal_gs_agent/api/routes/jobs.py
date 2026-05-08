"""Job submission routes."""

import os

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
    JobReportResponse,
    JobStatusResponse,
    JobSubmissionRequest,
    JobSubmissionResponse,
)
from animal_gs_agent.services.artifact_service import list_artifacts
from animal_gs_agent.services.dataset_profile_service import build_dataset_profile
from animal_gs_agent.services.job_service import (
    create_job,
    get_job,
    mark_job_queued_for_worker,
    refresh_running_job,
    run_job,
)
from animal_gs_agent.services.report_service import build_job_report
from animal_gs_agent.services.run_queue_service import enqueue_run_job
from animal_gs_agent.services.slurm_service import poll_slurm_job_state
from animal_gs_agent.services.workflow_result_service import parse_workflow_outputs
from animal_gs_agent.services.workflow_service import execute_fixed_workflow


def create_jobs_router() -> APIRouter:
    router = APIRouter()

    @router.post(
        "/jobs",
        response_model=JobSubmissionResponse,
        response_model_exclude_none=True,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def submit_job(payload: JobSubmissionRequest) -> JobSubmissionResponse:
        settings = get_settings()
        if not settings.llm.base_url or not settings.llm.api_key or not settings.llm.model:
            raise HTTPException(status_code=503, detail="LLM provider is not configured")

        client = OpenAICompatibleLLMClient(settings.llm)
        try:
            task_understanding = understand_task(payload.user_message, llm_client=client)
        except (TaskUnderstandingProviderError, TaskUnderstandingValidationError) as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        dataset_profile = build_dataset_profile(payload)
        return create_job(
            payload,
            task_understanding=task_understanding,
            dataset_profile=dataset_profile,
        )

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

    return router
