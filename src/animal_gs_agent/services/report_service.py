"""Agent-facing report generation service."""

import os

from animal_gs_agent.schemas.jobs import JobReportResponse, JobStatusResponse, RoleSpecificReport
from animal_gs_agent.services.audit_service import build_claim_evidence_map, run_audit_checks
from animal_gs_agent.services.benchmark_service import (
    build_ablation_benchmark,
    build_baseline_benchmark,
    export_plot_artifact,
)
from animal_gs_agent.services.knowledge_service import (
    build_knowledge_documents,
    build_recommendation_citations,
)


def _csv_env_paths(name: str) -> list[str]:
    raw = os.getenv(name, "")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(1, value)


def _build_role_reports(
    *,
    job: JobStatusResponse,
    top_preview: str,
    recommendations: list[str],
    risk_tags: list[str],
    audit_checks,
) -> tuple[list[RoleSpecificReport], bool, str | None]:
    top1 = job.workflow_summary.top_candidates[0] if job.workflow_summary and job.workflow_summary.top_candidates else None
    top1_text = f"{top1.individual_id} (GEBV={top1.gebv:.4f})" if top1 else "no candidate"
    shared_conclusion = f"Top recommendation is {top1_text} for trait `{job.trait_name}`."
    audit_risk_count = sum(1 for item in audit_checks if item.status == "risk")
    audit_summary = f"audit: {audit_risk_count} risk checks, {len(audit_checks) - audit_risk_count} pass checks"
    risk_text = ", ".join(risk_tags) if risk_tags else "none"
    recommendation_text = " | ".join(recommendations) if recommendations else "none"
    risk_summary = f"risk tags: {risk_text}; recommendation: {recommendation_text}"

    reports = [
        RoleSpecificReport(
            role="technical",
            conclusion=shared_conclusion,
            summary=(
                f"Model metrics: {job.workflow_summary.model_metrics}. "
                f"Top candidates preview: {top_preview}."
            ),
            audit_summary=audit_summary,
            risk_summary=risk_summary,
        ),
        RoleSpecificReport(
            role="decision",
            conclusion=shared_conclusion,
            summary=(
                f"Decision basis combines workflow ranking and recommendation signals. "
                f"Selected top candidate: {top1_text}."
            ),
            audit_summary=audit_summary,
            risk_summary=risk_summary,
        ),
        RoleSpecificReport(
            role="management",
            conclusion=shared_conclusion,
            summary=(
                "Execution completed with auditable trail and evidence-linked recommendation. "
                f"Outcome summary: {top_preview}."
            ),
            audit_summary=audit_summary,
            risk_summary=risk_summary,
        ),
    ]
    unique_conclusions = {item.conclusion for item in reports}
    alignment_ok = len(unique_conclusions) == 1
    alignment_note = None if alignment_ok else "role reports are not aligned on final conclusion"
    return reports, alignment_ok, alignment_note


def build_job_report(job: JobStatusResponse) -> JobReportResponse:
    if job.workflow_summary is None:
        raise ValueError("workflow summary is not available")

    fixed_effects = ", ".join(job.task_understanding.candidate_fixed_effects) or "none"
    top_preview = ", ".join(
        f"{item.rank}:{item.individual_id}({item.gebv:.4f})"
        for item in job.workflow_summary.top_candidates[:5]
    ) or "no candidates"
    risk_tags = job.dataset_profile.risk_tags
    risk_text = ", ".join(risk_tags) if risk_tags else "none"
    diagnostics = job.dataset_profile.phenotype_diagnostics
    recommendations = diagnostics.recommendations if diagnostics is not None else []
    recommendation_text = " | ".join(recommendations) if recommendations else "none"

    report_text = (
        f"Agent layer: interpreted trait `{job.trait_name}`, extracted fixed effects [{fixed_effects}], "
        f"and validated dataset structure before execution (risk tags: {risk_text}).\n"
        f"Agent recommendation: {recommendation_text}.\n"
        f"Workflow layer: executed `{job.workflow_backend}` and produced ranked GEBV outputs from fixed GS pipeline.\n"
        f"Top candidates preview: {top_preview}."
    )

    claim_evidence_map = build_claim_evidence_map(job)
    audit_checks = run_audit_checks(job)
    from animal_gs_agent.services.job_service import jobs_store

    history_jobs = [item for item in jobs_store.values() if item.status == "completed"]
    sop_paths = _csv_env_paths("ANIMAL_GS_AGENT_KNOWLEDGE_SOP_PATHS")
    literature_paths = _csv_env_paths("ANIMAL_GS_AGENT_KNOWLEDGE_LITERATURE_PATHS")
    knowledge_docs = build_knowledge_documents(
        history_jobs=history_jobs,
        sop_paths=sop_paths,
        literature_paths=literature_paths,
    )
    knowledge_citations = build_recommendation_citations(
        recommendations=recommendations,
        documents=knowledge_docs,
        top_k_per_recommendation=_int_env("ANIMAL_GS_AGENT_KNOWLEDGE_TOP_K", 2),
    )
    role_reports, alignment_ok, alignment_note = _build_role_reports(
        job=job,
        top_preview=top_preview,
        recommendations=recommendations,
        risk_tags=risk_tags,
        audit_checks=audit_checks,
    )
    benchmark_baseline = build_baseline_benchmark(
        job=job,
        random_seed=_int_env("ANIMAL_GS_AGENT_BENCHMARK_RANDOM_SEED", 42),
    )
    benchmark_ablation = build_ablation_benchmark(baseline_report=benchmark_baseline)
    benchmark_plot_artifact = export_plot_artifact(
        job_id=job.job_id,
        baseline_report=benchmark_baseline,
        ablation_report=benchmark_ablation,
    )

    return JobReportResponse(
        job_id=job.job_id,
        trait_name=job.trait_name,
        status=job.status,
        report_text=report_text,
        top_candidates=job.workflow_summary.top_candidates,
        claim_evidence_map=claim_evidence_map,
        audit_checks=audit_checks,
        knowledge_citations=knowledge_citations,
        role_reports=role_reports,
        role_report_alignment_ok=alignment_ok,
        role_report_alignment_note=alignment_note,
        benchmark_baseline=benchmark_baseline,
        benchmark_ablation=benchmark_ablation,
        benchmark_plot_artifact=benchmark_plot_artifact,
    )
