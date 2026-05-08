"""Minimal job service."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
from uuid import uuid4

from animal_gs_agent.schemas.jobs import (
    DecisionTraceNode,
    FallbackPlan,
    JobEvent,
    JobStatusResponse,
    JobSubmissionRequest,
    JobSubmissionResponse,
)
from animal_gs_agent.schemas.dataset_profile import DatasetProfile
from animal_gs_agent.schemas.task_understanding import TaskUnderstandingResult
from animal_gs_agent.services.workflow_service import WorkflowExecutionError
from animal_gs_agent.services.model_pool_service import build_model_pool_plan
from animal_gs_agent.services.trial_orchestrator_service import build_trial_plan
from animal_gs_agent.services.validation_protocol_service import build_validation_protocol_plan
from animal_gs_agent.services.badcase_service import build_badcase_advice
from animal_gs_agent.services.debug_service import build_debug_diagnosis

jobs_store: dict[str, JobStatusResponse] = {}


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _append_event(job: JobStatusResponse, phase: str, message: str, error_code: str | None = None) -> list[JobEvent]:
    return [
        *job.events,
        JobEvent(
            phase=phase,  # type: ignore[arg-type]
            timestamp=_now_iso(),
            message=message,
            error_code=error_code,
        ),
    ]


def _append_decision(
    job: JobStatusResponse,
    *,
    decision_id: str,
    action: str,
    rationale: str,
    status: str,
    duration_ms: int,
    confidence: float,
    evidence: list[str] | None = None,
    input_summary: str | None = None,
    output_summary: str | None = None,
    counterfactual: str | None = None,
    feature_id: str = "F-P0-01-02",
    story_id: str | None = None,
    agent_id: str = "supervisor",
) -> list[DecisionTraceNode]:
    return [
        *job.decision_trace,
        DecisionTraceNode(
            decision_id=decision_id,
            feature_id=feature_id,
            story_id=story_id,
            agent_id=agent_id,
            action=action,
            rationale=rationale,
            status=status,  # type: ignore[arg-type]
            duration_ms=duration_ms,
            confidence=confidence,
            evidence=evidence or [],
            input_summary=input_summary,
            output_summary=output_summary,
            counterfactual=counterfactual,
            timestamp=_now_iso(),
        ),
    ]


def _job_store_path() -> Path | None:
    raw = os.getenv("ANIMAL_GS_AGENT_JOB_STORE_PATH")
    if raw is None or not raw.strip():
        return None
    return Path(raw)


def _job_store_sqlite_path() -> Path | None:
    raw = os.getenv("ANIMAL_GS_AGENT_JOB_STORE_SQLITE_PATH")
    if raw is None or not raw.strip():
        return None
    return Path(raw)


def _trace_output_dir(job: JobStatusResponse) -> Path:
    if job.workflow_result_dir and job.workflow_result_dir.strip():
        return Path(job.workflow_result_dir)
    root = Path(
        os.getenv(
            "ANIMAL_GS_AGENT_TRACE_OUTPUT_ROOT",
            os.getenv(
                "ANIMAL_GS_AGENT_WORKFLOW_OUTPUT_ROOT",
                "/work/home/zyqlab/dzhichao/Agent0428/animal_gs_agent/runs",
            ),
        )
    )
    return root / job.job_id


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError:
        return default
    return value


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name, str(default))
    try:
        value = float(raw)
    except ValueError:
        return default
    return value


def _optional_int_env(name: str) -> int | None:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _persist_decision_trace_file(job: JobStatusResponse) -> None:
    trace_dir = _trace_output_dir(job)
    trace_dir.mkdir(parents=True, exist_ok=True)
    trace_path = trace_dir / "decision_trace.json"
    payload = {
        "job_id": job.job_id,
        "status": job.status,
        "decision_trace": [node.model_dump() for node in job.decision_trace],
    }
    trace_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _sqlite_init(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _sqlite_load(path: Path) -> dict[str, JobStatusResponse]:
    _sqlite_init(path)
    loaded: dict[str, JobStatusResponse] = {}
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT job_id, payload FROM jobs").fetchall()
    for job_id, payload in rows:
        loaded[job_id] = JobStatusResponse.model_validate_json(payload)
    return loaded


def _sqlite_persist(path: Path) -> None:
    _sqlite_init(path)
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM jobs")
        conn.executemany(
            "INSERT INTO jobs(job_id, payload) VALUES(?, ?)",
            [(job_id, job.model_dump_json()) for job_id, job in jobs_store.items()],
        )
        conn.commit()


def _sqlite_load_job(path: Path, job_id: str) -> JobStatusResponse | None:
    _sqlite_init(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    if row is None:
        return None
    return JobStatusResponse.model_validate_json(row[0])


def _json_load_job(path: Path, job_id: str) -> JobStatusResponse | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw = payload.get(job_id)
    if raw is None:
        return None
    return JobStatusResponse.model_validate(raw)


def _reload_job_from_persistence(job_id: str) -> JobStatusResponse | None:
    sqlite_path = _job_store_sqlite_path()
    if sqlite_path is not None:
        job = _sqlite_load_job(sqlite_path, job_id)
        if job is not None:
            jobs_store[job_id] = job
        return job

    json_path = _job_store_path()
    if json_path is None:
        return None
    job = _json_load_job(json_path, job_id)
    if job is not None:
        jobs_store[job_id] = job
    return job


def _load_store_if_needed() -> None:
    if jobs_store:
        return
    sqlite_path = _job_store_sqlite_path()
    if sqlite_path is not None:
        jobs_store.update(_sqlite_load(sqlite_path))
        return
    path = _job_store_path()
    if path is None or not path.exists():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    for job_id, raw in payload.items():
        jobs_store[job_id] = JobStatusResponse.model_validate(raw)


def _persist_store_if_needed() -> None:
    sqlite_path = _job_store_sqlite_path()
    if sqlite_path is not None:
        _sqlite_persist(sqlite_path)
        for job in jobs_store.values():
            _persist_decision_trace_file(job)
        return
    path = _job_store_path()
    if path is None:
        for job in jobs_store.values():
            _persist_decision_trace_file(job)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {job_id: job.model_dump() for job_id, job in jobs_store.items()}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    for job in jobs_store.values():
        _persist_decision_trace_file(job)


def create_job(
    payload: JobSubmissionRequest,
    task_understanding: TaskUnderstandingResult,
    dataset_profile: DatasetProfile,
) -> JobSubmissionResponse:
    _load_store_if_needed()
    historical_jobs = [job for job in jobs_store.values() if job.status in {"completed", "failed"}]
    model_pool_plan = build_model_pool_plan(task_understanding, dataset_profile)
    trial_strategy_plan = build_trial_plan(
        max_trials=max(1, _int_env("ANIMAL_GS_AGENT_STRATEGY_MAX_TRIALS", 5)),
        candidate_models=model_pool_plan.available_models,
        random_seed=_optional_int_env("ANIMAL_GS_AGENT_STRATEGY_RANDOM_SEED"),
        early_stop_patience=max(1, _int_env("ANIMAL_GS_AGENT_STRATEGY_EARLY_STOP_PATIENCE", 3)),
        min_improvement=_float_env("ANIMAL_GS_AGENT_STRATEGY_MIN_IMPROVEMENT", 0.0),
    )
    validation_protocol_plan = build_validation_protocol_plan(task_understanding, dataset_profile)
    badcase_advice = build_badcase_advice(
        task_understanding=task_understanding,
        dataset_profile=dataset_profile,
        historical_jobs=historical_jobs,
        similarity_threshold=_float_env("ANIMAL_GS_AGENT_BADCASE_SIMILARITY_THRESHOLD", 0.50),
        top_k=max(1, _int_env("ANIMAL_GS_AGENT_BADCASE_TOP_K", 3)),
    )
    job = JobStatusResponse(
        job_id=uuid4().hex[:8],
        status="queued",
        trait_name=payload.trait_name,
        task_understanding=task_understanding,
        dataset_profile=dataset_profile,
        model_pool_plan=model_pool_plan,
        trial_strategy_plan=trial_strategy_plan,
        validation_protocol_plan=validation_protocol_plan,
        badcase_advice=badcase_advice,
        events=[
            JobEvent(
                phase="queued",
                timestamp=_now_iso(),
                message="job accepted and queued",
            )
        ],
        decision_trace=[
            DecisionTraceNode(
                decision_id="intake_accept_job",
                feature_id="F-P0-01-02",
                story_id="S-P0-01-03",
                agent_id="supervisor",
                action="accept_job",
                rationale="request passed intake parsing and was admitted to job queue",
                status="success",
                duration_ms=5,
                confidence=0.95,
                evidence=[f"trait={payload.trait_name}", f"scope={task_understanding.request_scope}"],
                input_summary=payload.user_message,
                output_summary="job status=queued",
                timestamp=_now_iso(),
            )
        ],
    )
    jobs_store[job.job_id] = job
    _persist_store_if_needed()
    return JobSubmissionResponse(**job.model_dump())


def get_job(job_id: str) -> JobStatusResponse | None:
    _load_store_if_needed()
    reloaded = _reload_job_from_persistence(job_id)
    if reloaded is not None:
        return reloaded
    return jobs_store.get(job_id)


def mark_job_queued_for_worker(job_id: str) -> JobStatusResponse | None:
    _load_store_if_needed()
    job = jobs_store.get(job_id)
    if job is None:
        return None
    if job.status in {"running", "completed"}:
        return job
    updated = job.model_copy(
        update={
            "status": "queued",
            "execution_error": None,
            "execution_error_detail": None,
            "escalation_required": False,
            "escalation_reason": None,
            "escalation_requested_at": None,
            "fallback_plan": None,
            "events": _append_event(job, phase="queued", message="queued for async worker execution"),
        }
    )
    jobs_store[job_id] = updated
    _persist_store_if_needed()
    return updated


def mark_job_escalated(job_id: str, reason: str, *, evidence: list[str] | None = None) -> JobStatusResponse | None:
    _load_store_if_needed()
    job = jobs_store.get(job_id)
    if job is None:
        return None
    now = _now_iso()
    escalated = job.model_copy(
        update={
            "status": "failed",
            "escalation_required": True,
            "escalation_reason": reason,
            "escalation_requested_at": now,
            "escalation_resolution": None,
            "escalation_resolved_by": None,
            "escalation_resolved_at": None,
            "fallback_plan": None,
            "execution_error": "worker_retry_budget_exhausted",
            "execution_error_detail": f"manual escalation required: {reason}",
            "events": _append_event(
                job,
                phase="failed",
                message="worker retry budget exhausted; escalation required",
                error_code="worker_retry_budget_exhausted",
            ),
            "decision_trace": _append_decision(
                job,
                decision_id="worker_retry_budget_exhausted",
                action="escalate_human_review",
                rationale="automatic retries exceeded configured budget",
                status="failed",
                duration_ms=80,
                confidence=0.99,
                evidence=evidence or [],
                output_summary="job escalated to manual review",
                feature_id="F-P0-01-01",
                story_id="S-P0-01-02",
            ),
        }
    )
    jobs_store[job_id] = escalated
    _persist_store_if_needed()
    return escalated


def resolve_job_escalation_retry(job_id: str, approver: str, reason: str) -> JobStatusResponse | None:
    _load_store_if_needed()
    job = jobs_store.get(job_id)
    if job is None:
        return None
    if not job.escalation_required:
        raise ValueError(f"Job {job_id} is not waiting for escalation resolution")

    now = _now_iso()
    updated = job.model_copy(
        update={
            "status": "queued",
            "escalation_required": False,
            "escalation_reason": None,
            "escalation_resolution": "retry",
            "escalation_resolved_by": approver,
            "escalation_resolved_at": now,
            "fallback_plan": None,
            "execution_error": None,
            "execution_error_detail": None,
            "events": _append_event(
                job,
                phase="queued",
                message=f"escalation approved for retry by {approver}",
            ),
            "decision_trace": _append_decision(
                job,
                decision_id="manual_escalation_retry_approved",
                action="approve_escalation_retry",
                rationale=f"human approver requested retry: {reason}",
                status="success",
                duration_ms=60,
                confidence=0.99,
                evidence=[f"approver={approver}", f"reason={reason}"],
                output_summary="job re-queued after escalation review",
                feature_id="F-P1-04-01",
                story_id="S-P1-04-01",
            ),
        }
    )
    jobs_store[job_id] = updated
    _persist_store_if_needed()
    return updated


def resolve_job_escalation_abort(job_id: str, approver: str, reason: str) -> JobStatusResponse | None:
    _load_store_if_needed()
    job = jobs_store.get(job_id)
    if job is None:
        return None
    if not job.escalation_required:
        raise ValueError(f"Job {job_id} is not waiting for escalation resolution")

    now = _now_iso()
    updated = job.model_copy(
        update={
            "status": "failed",
            "escalation_required": False,
            "escalation_reason": None,
            "escalation_resolution": "abort",
            "escalation_resolved_by": approver,
            "escalation_resolved_at": now,
            "fallback_plan": FallbackPlan(
                strategy="manual_review_with_fixed_pipeline_fallback",
                reason=reason,
                created_by=approver,
                created_at=now,
            ),
            "execution_error": "manual_abort_after_escalation",
            "execution_error_detail": f"aborted by {approver}: {reason}",
            "events": _append_event(
                job,
                phase="failed",
                message=f"escalation resolved as abort by {approver}",
                error_code="manual_abort_after_escalation",
            ),
            "decision_trace": _append_decision(
                job,
                decision_id="manual_escalation_abort_approved",
                action="approve_escalation_abort",
                rationale=f"human approver terminated run: {reason}",
                status="success",
                duration_ms=55,
                confidence=0.99,
                evidence=[f"approver={approver}", f"reason={reason}"],
                output_summary="job marked failed by escalation abort",
                feature_id="F-P1-04-01",
                story_id="S-P1-04-01",
            ),
        }
    )
    jobs_store[job_id] = updated
    _persist_store_if_needed()
    return updated


def resolve_qc_block_override(job_id: str, approver: str, reason: str) -> JobStatusResponse | None:
    _load_store_if_needed()
    job = jobs_store.get(job_id)
    if job is None:
        return None
    if job.execution_error != "qc_risk_high_blocked":
        raise ValueError(f"Job {job_id} is not waiting for qc override")

    now = _now_iso()
    updated = job.model_copy(
        update={
            "status": "queued",
            "execution_error": None,
            "execution_error_detail": None,
            "qc_override_applied": True,
            "qc_override_by": approver,
            "qc_override_reason": reason,
            "qc_override_at": now,
            "events": _append_event(
                job,
                phase="queued",
                message=f"qc override approved by {approver}",
            ),
            "decision_trace": _append_decision(
                job,
                decision_id="manual_qc_override_approved",
                action="approve_qc_override",
                rationale=f"human approver accepted high-qc-risk run: {reason}",
                status="success",
                duration_ms=45,
                confidence=0.99,
                evidence=[f"approver={approver}", f"reason={reason}"],
                output_summary="qc block cleared, job re-queued",
                feature_id="F-P0-02-01",
                story_id="S-P0-02-05",
            ),
        }
    )
    jobs_store[job_id] = updated
    _persist_store_if_needed()
    return updated


def refresh_running_job(
    job_id: str,
    slurm_state_checker=None,
    workflow_output_parser=None,
) -> JobStatusResponse | None:
    _load_store_if_needed()
    _reload_job_from_persistence(job_id)
    job = jobs_store.get(job_id)
    if job is None:
        return None
    if job.status != "running":
        return job
    if job.workflow_backend != "slurm_nextflow_submit":
        return job
    if not job.workflow_submission_id:
        return job
    if slurm_state_checker is None:
        return job

    queue_state = slurm_state_checker(job.workflow_submission_id)
    if queue_state in {"PENDING", "RUNNING", "UNKNOWN"}:
        updated = job.model_copy(
            update={
                "workflow_queue_state": queue_state,
                "decision_trace": _append_decision(
                    job,
                    decision_id=f"slurm_poll_{queue_state.lower()}",
                    action="poll_slurm_state",
                    rationale="polling remote scheduler to refresh runtime state",
                    status="running",
                    duration_ms=120,
                    confidence=0.9,
                    evidence=[f"submission_id={job.workflow_submission_id}", f"queue_state={queue_state}"],
                    output_summary=f"job remains {job.status}",
                    story_id="S-P0-01-03",
                ),
            }
        )
        jobs_store[job_id] = updated
        _persist_store_if_needed()
        return updated

    if queue_state == "COMPLETED":
        workflow_summary = None
        if workflow_output_parser is not None and job.workflow_result_dir:
            try:
                workflow_summary = workflow_output_parser(
                    result_dir=job.workflow_result_dir,
                    trait_name=job.trait_name,
                )
            except Exception:
                failed = job.model_copy(
                    update={
                        "status": "failed",
                        "workflow_queue_state": queue_state,
                        "execution_error": "workflow_output_parse_error",
                        "execution_error_detail": "failed to parse fixed workflow outputs",
                        "events": _append_event(
                            job,
                            phase="failed",
                            message="workflow output parsing failed after slurm completion",
                            error_code="workflow_output_parse_error",
                        ),
                        "decision_trace": _append_decision(
                            job,
                            decision_id="slurm_complete_parse_failed",
                            action="finalize_failed",
                            rationale="workflow finished but output parsing failed",
                            status="failed",
                            duration_ms=220,
                            confidence=0.92,
                            evidence=["error=workflow_output_parse_error"],
                            output_summary="job status=failed",
                            story_id="S-P0-01-03",
                        ),
                    }
                )
                jobs_store[job_id] = failed
                _persist_store_if_needed()
                return failed

        completed = job.model_copy(
            update={
                "status": "completed",
                "workflow_queue_state": queue_state,
                "execution_error": None,
                "execution_error_detail": None,
                "workflow_summary": workflow_summary,
                "events": _append_event(
                    job,
                    phase="completed",
                    message=f"slurm workflow finished ({queue_state})",
                ),
                "decision_trace": _append_decision(
                    job,
                    decision_id="slurm_complete_success",
                    action="finalize_completed",
                    rationale="scheduler reported completion and outputs were parseable",
                    status="success",
                    duration_ms=240,
                    confidence=0.95,
                    evidence=[f"queue_state={queue_state}", f"result_dir={job.workflow_result_dir or 'unknown'}"],
                    output_summary="job status=completed",
                    story_id="S-P0-01-03",
                ),
            }
        )
        jobs_store[job_id] = completed
        _persist_store_if_needed()
        return completed

    failed = job.model_copy(
        update={
            "status": "failed",
            "workflow_queue_state": queue_state,
            "execution_error": "workflow_slurm_failed",
            "execution_error_detail": f"slurm job state: {queue_state}",
            "events": _append_event(
                job,
                phase="failed",
                message=f"slurm workflow failed ({queue_state})",
                error_code="workflow_slurm_failed",
            ),
            "decision_trace": _append_decision(
                job,
                decision_id=f"slurm_terminal_{queue_state.lower()}",
                action="finalize_failed",
                rationale="scheduler returned terminal non-success state",
                status="failed",
                duration_ms=200,
                confidence=0.94,
                evidence=[f"queue_state={queue_state}"],
                output_summary="job status=failed",
                story_id="S-P0-01-03",
            ),
        }
    )
    jobs_store[job_id] = failed
    _persist_store_if_needed()
    return failed


def run_job(job_id: str, workflow_executor=None, workflow_output_parser=None) -> JobStatusResponse | None:
    _load_store_if_needed()
    job = jobs_store.get(job_id)
    if job is None:
        return None
    if job.status in {"running", "completed"}:
        return job

    running_job = job.model_copy(
        update={
            "status": "running",
            "execution_error": None,
            "execution_error_detail": None,
            "debug_diagnosis": None,
            "events": _append_event(job, phase="running", message="workflow execution started"),
            "decision_trace": _append_decision(
                job,
                decision_id="run_workflow_started",
                action="start_workflow",
                rationale="job dequeued and workflow execution began",
                status="running",
                duration_ms=30,
                confidence=0.9,
                evidence=[f"job_id={job_id}"],
                output_summary="job status=running",
                story_id="S-P0-01-02",
            ),
        }
    )
    jobs_store[job_id] = running_job
    _persist_store_if_needed()

    validation_flags = list(running_job.dataset_profile.validation_flags)
    if running_job.qc_override_applied:
        validation_flags = [flag for flag in validation_flags if flag != "qc_risk_high"]

    first_error = next(iter(validation_flags), None)
    if first_error is not None:
        error_code = first_error
        error_detail = "dataset validation failed before workflow execution"
        rationale = "dataset validation failed prior to workflow launch"
        evidence = [f"validation_error={first_error}"]
        feature_id = "F-P0-01-01"
        story_id = "S-P0-01-02"
        if first_error == "qc_risk_high":
            error_code = "qc_risk_high_blocked"
            error_detail = "qc risk gate blocked run; manual override required"
            rationale = "qc risk exceeded configured threshold and no override was present"
            evidence = [
                f"qc_risk_level={running_job.dataset_profile.qc_risk_level}",
                f"trait={running_job.trait_name}",
            ]
            feature_id = "F-P0-02-01"
            story_id = "S-P0-02-05"

        failed_job = running_job.model_copy(
            update={
                "status": "failed",
                "execution_error": error_code,
                "execution_error_detail": error_detail,
                "debug_diagnosis": build_debug_diagnosis(
                    error_code=error_code,
                    error_message=error_detail,
                    attempt=1,
                    max_attempts=max(1, _int_env("ANIMAL_GS_AGENT_RUN_QUEUE_MAX_ATTEMPTS", 3)),
                ),
                "events": _append_event(
                    running_job,
                    phase="failed",
                    message="dataset validation failed",
                    error_code=error_code,
                ),
                "decision_trace": _append_decision(
                    running_job,
                    decision_id="preflight_dataset_failed",
                    action="block_execution",
                    rationale=rationale,
                    status="failed",
                    duration_ms=25,
                    confidence=0.98,
                    evidence=evidence,
                    output_summary="job status=failed",
                    feature_id=feature_id,
                    story_id=story_id,
                ),
            }
        )
        jobs_store[job_id] = failed_job
        _persist_store_if_needed()
        return failed_job

    if workflow_executor is not None:
        try:
            execution_result = workflow_executor(running_job)
        except WorkflowExecutionError as exc:
            failed_job = running_job.model_copy(
                update={
                    "status": "failed",
                    "execution_error": exc.code,
                    "execution_error_detail": exc.message,
                    "debug_diagnosis": build_debug_diagnosis(
                        error_code=exc.code,
                        error_message=exc.message,
                        attempt=1,
                        max_attempts=max(1, _int_env("ANIMAL_GS_AGENT_RUN_QUEUE_MAX_ATTEMPTS", 3)),
                    ),
                    "events": _append_event(
                        running_job,
                        phase="failed",
                        message="workflow execution failed",
                        error_code=exc.code,
                    ),
                    "decision_trace": _append_decision(
                        running_job,
                        decision_id="workflow_runtime_failed",
                        action="finalize_failed",
                        rationale="workflow executor raised runtime failure",
                        status="failed",
                        duration_ms=350,
                        confidence=0.96,
                        evidence=[f"error_code={exc.code}"],
                        output_summary="job status=failed",
                        story_id="S-P0-01-02",
                    ),
                }
            )
            jobs_store[job_id] = failed_job
            _persist_store_if_needed()
            return failed_job

        if execution_result.status == "submitted":
            submitted_job = running_job.model_copy(
                update={
                    "status": "running",
                    "execution_error": None,
                    "execution_error_detail": None,
                    "workflow_backend": execution_result.backend,
                    "workflow_result_dir": execution_result.result_dir,
                    "workflow_submission_id": execution_result.submission_id,
                    "workflow_queue_state": "PENDING",
                    "events": _append_event(
                        running_job,
                        phase="running",
                        message=f"submitted workflow to slurm ({execution_result.submission_id or 'unknown_job_id'})",
                    ),
                    "decision_trace": _append_decision(
                        running_job,
                        decision_id="workflow_submitted_slurm",
                        action="submit_slurm",
                        rationale="execution policy routed workflow to slurm backend",
                        status="running",
                        duration_ms=180,
                        confidence=0.93,
                        evidence=[f"submission_id={execution_result.submission_id or 'unknown_job_id'}"],
                        output_summary="job status=running",
                        story_id="S-P0-01-02",
                    ),
                }
            )
            jobs_store[job_id] = submitted_job
            _persist_store_if_needed()
            return submitted_job

        workflow_summary = None
        if workflow_output_parser is not None:
            try:
                workflow_summary = workflow_output_parser(
                    result_dir=execution_result.result_dir,
                    trait_name=running_job.trait_name,
                )
            except Exception:
                failed_job = running_job.model_copy(
                    update={
                        "status": "failed",
                        "execution_error": "workflow_output_parse_error",
                        "execution_error_detail": "failed to parse fixed workflow outputs",
                        "debug_diagnosis": build_debug_diagnosis(
                            error_code="workflow_output_parse_error",
                            error_message="failed to parse fixed workflow outputs",
                            attempt=1,
                            max_attempts=max(1, _int_env("ANIMAL_GS_AGENT_RUN_QUEUE_MAX_ATTEMPTS", 3)),
                        ),
                        "events": _append_event(
                            running_job,
                            phase="failed",
                            message="workflow output parsing failed",
                            error_code="workflow_output_parse_error",
                        ),
                        "decision_trace": _append_decision(
                            running_job,
                            decision_id="workflow_parse_failed",
                            action="finalize_failed",
                            rationale="workflow ran but outputs could not be parsed",
                            status="failed",
                            duration_ms=260,
                            confidence=0.95,
                            evidence=["error=workflow_output_parse_error"],
                            output_summary="job status=failed",
                            story_id="S-P0-01-03",
                        ),
                    }
                )
                jobs_store[job_id] = failed_job
                _persist_store_if_needed()
                return failed_job

        completed_job = running_job.model_copy(
            update={
                "status": "completed",
                "execution_error": None,
                "execution_error_detail": None,
                "workflow_backend": execution_result.backend,
                "workflow_result_dir": execution_result.result_dir,
                "workflow_summary": workflow_summary,
                "events": _append_event(
                    running_job,
                    phase="completed",
                    message="workflow execution and parsing completed",
                ),
                "decision_trace": _append_decision(
                    running_job,
                    decision_id="workflow_completed_success",
                    action="finalize_completed",
                    rationale="workflow and parser both completed successfully",
                    status="success",
                    duration_ms=420,
                    confidence=0.97,
                    evidence=[f"backend={execution_result.backend}", f"result_dir={execution_result.result_dir}"],
                    output_summary="job status=completed",
                    story_id="S-P0-01-03",
                ),
            }
        )
        jobs_store[job_id] = completed_job
        _persist_store_if_needed()
        return completed_job

    completed_job = running_job.model_copy(
        update={
            "status": "completed",
            "execution_error": None,
            "execution_error_detail": None,
            "events": _append_event(
                running_job,
                phase="completed",
                message="job completed without external workflow executor",
            ),
            "decision_trace": _append_decision(
                running_job,
                decision_id="workflow_bypass_completed",
                action="finalize_completed",
                rationale="no external workflow executor configured; synthetic completion path",
                status="success",
                duration_ms=40,
                confidence=0.75,
                output_summary="job status=completed",
                story_id="S-P0-01-03",
            ),
        }
    )
    jobs_store[job_id] = completed_job
    _persist_store_if_needed()
    return completed_job
