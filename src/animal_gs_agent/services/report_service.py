"""Agent-facing report generation service."""

from animal_gs_agent.schemas.jobs import JobReportResponse, JobStatusResponse


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

    return JobReportResponse(
        job_id=job.job_id,
        trait_name=job.trait_name,
        status=job.status,
        report_text=report_text,
        top_candidates=job.workflow_summary.top_candidates,
    )
