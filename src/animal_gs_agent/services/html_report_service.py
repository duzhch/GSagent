"""Standalone HTML report export for GS candidate decisions."""

from __future__ import annotations

from html import escape
import math
import os
from pathlib import Path

from animal_gs_agent.schemas.benchmark import PlotExportArtifact
from animal_gs_agent.schemas.jobs import JobStatusResponse, RankedCandidate


def _report_output_dir(job: JobStatusResponse, output_root: Path | None) -> Path:
    if output_root is not None:
        return output_root / job.job_id
    if job.workflow_result_dir and job.workflow_result_dir.strip():
        return Path(job.workflow_result_dir)
    configured = os.getenv("ANIMAL_GS_AGENT_HTML_REPORT_OUTPUT_ROOT", "").strip()
    root = Path(configured) if configured else Path("/tmp/animal_gs_agent_reports")
    return root / job.job_id


def _metric(metrics: dict[str, str], *keys: str) -> str:
    for key in keys:
        raw = metrics.get(key)
        if raw:
            return raw
    return "NA"


def _selection_label(rank: int) -> str:
    if rank <= 3:
        return "Priority selection candidate"
    if rank <= 10:
        return "Validation shortlist"
    return "Monitor only"


def _candidate_rows(candidates: list[RankedCandidate]) -> str:
    rows: list[str] = []
    for candidate in candidates:
        rows.append(
            "<tr>"
            f"<td>{candidate.rank}</td>"
            f"<td>{escape(candidate.individual_id)}</td>"
            f"<td>{candidate.gebv:.4f}</td>"
            f"<td>{escape(_selection_label(candidate.rank))}</td>"
            "</tr>"
    )
    return "\n".join(rows)


def _candidate_rows_autogs(candidates: list[RankedCandidate], trait_name: str) -> str:
    if not candidates:
        return '<tr><td colspan="7">No candidate ranking data available.</td></tr>'

    rows: list[str] = []
    for candidate in candidates[:8]:
        priority = "***" if candidate.rank <= 3 else "*" if candidate.rank <= 10 else "ns"
        priority_color = "red" if candidate.rank <= 3 else "orange" if candidate.rank <= 10 else "inherit"
        rows.append(
            "<tr>"
            f"<td>{candidate.rank}</td>"
            f"<td>{escape(candidate.individual_id)}</td>"
            f"<td>{candidate.gebv:.4f}</td>"
            f"<td>{escape(_selection_label(candidate.rank))}</td>"
            f"<td>{escape(trait_name)}</td>"
            "<td>GBLUP</td>"
            f'<td style="color:{priority_color}">{priority}</td>'
            "</tr>"
        )
    if len(candidates) > 8:
        rows.append(
            "<tr>"
            "<td>...</td><td>...</td><td>...</td><td>...</td>"
            f"<td>{escape(trait_name)}</td><td>...</td><td></td>"
            "</tr>"
        )
    return "\n".join(rows)


def _gebv_preview_bars(candidates: list[RankedCandidate]) -> str:
    if not candidates:
        return (
            '<div style="height: 100px; border-bottom: 2px solid #333; display: flex; '
            'align-items: center; justify-content: center; color: #666; font-size: 12px;">'
            "No GEBV data available.</div>"
        )

    top = candidates[:16]
    max_abs = max(abs(item.gebv) for item in top) or 1.0
    bars: list[str] = []
    for item in top:
        height = max(6, int((abs(item.gebv) / max_abs) * 88))
        color = "red" if item.rank <= 3 else "orange" if item.rank <= 10 else "#888"
        bars.append(
            f'<div title="#{item.rank} {escape(item.individual_id)} GEBV={item.gebv:.4f}" '
            f'style="width: 8px; height: {height}px; background: {color};"></div>'
        )
    bars.append(
        '<div style="flex-grow: 1; text-align: center; align-self: center; '
        'color: #666; font-size: 12px;">(Candidate GEBV Ranking)</div>'
    )
    return (
        '<div style="height: 100px; border-bottom: 2px solid #333; display: flex; '
        'align-items: flex-end; gap: 2px; padding-bottom: 2px;">'
        + "\n".join(bars)
        + "</div>"
    )


def _candidate_svg(candidates: list[RankedCandidate]) -> str:
    if not candidates:
        return (
            '<svg viewBox="0 0 900 180" role="img" aria-label="No candidate data">'
            '<text x="40" y="92" fill="#53606f">No candidate ranking data available.</text>'
            "</svg>"
        )

    top = candidates[:10]
    max_abs = max(abs(item.gebv) for item in top) or 1.0
    chart_width = 610
    row_h = 34
    height = 70 + row_h * len(top)
    parts = [
        f'<svg viewBox="0 0 900 {height}" role="img" aria-label="Candidate GEBV Ranking">',
        '<text x="32" y="34" class="svg-title">Candidate GEBV Ranking</text>',
        '<line x1="220" y1="52" x2="830" y2="52" stroke="#d7dde4" stroke-width="1"/>',
    ]
    for idx, item in enumerate(top):
        y = 76 + idx * row_h
        bar_w = max(10, int((abs(item.gebv) / max_abs) * chart_width))
        label = f"#{item.rank} {item.individual_id}"
        score = f"{item.gebv:.4f}"
        parts.extend(
            [
                f'<text x="32" y="{y + 18}" class="svg-label">{escape(label)}</text>',
                f'<rect x="220" y="{y}" width="{bar_w}" height="20" rx="4" class="svg-bar"/>',
                f'<text x="{min(840, 230 + bar_w)}" y="{y + 15}" class="svg-score">{escape(score)}</text>',
            ]
        )
    parts.append("</svg>")
    return "\n".join(parts)


def _summary_stat(value: str) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return escape(value)
    if math.isfinite(number):
        return f"{number:.4f}"
    return "NA"


def _first_user_input(job: JobStatusResponse) -> str:
    for node in job.decision_trace:
        if node.input_summary:
            return node.input_summary
    return job.task_understanding.user_goal


def _plan_items(job: JobStatusResponse) -> str:
    fixed_effects = ", ".join(job.task_understanding.candidate_fixed_effects) or "none"
    items = [
        f"Interpret task intent: {job.task_understanding.user_goal}",
        f"Trait: {job.trait_name}; fixed effects considered: {fixed_effects}",
        (
            "Check phenotype/genotype input structure and QC risk tags: "
            f"{', '.join(job.dataset_profile.risk_tags) or 'none'}"
        ),
    ]
    if job.model_pool_plan is not None:
        models = ", ".join(job.model_pool_plan.available_models) or "no available model"
        items.append(f"Candidate model pool: {models}")
    else:
        items.append("Candidate model pool: fixed GBLUP pipeline")
    if job.trial_strategy_plan is not None:
        selected = job.trial_strategy_plan.selected_model or "not selected"
        items.append(
            "Search strategy: "
            f"selected_model={selected}; budget_consumed={job.trial_strategy_plan.budget_consumed}; "
            f"stop_reason={job.trial_strategy_plan.stop_reason}"
        )
    if job.validation_protocol_plan is not None and job.validation_protocol_plan.protocols:
        protocols = ", ".join(item.scenario_id for item in job.validation_protocol_plan.protocols)
        items.append(f"Validation protocol: {protocols}")
    else:
        items.append("Validation protocol: use workflow metrics and audit review for this run")
    return "\n".join(f"<li>{escape(item)}</li>" for item in items)


def _event_rows(job: JobStatusResponse) -> str:
    if not job.events:
        return '<tr><td colspan="3">No execution log recorded.</td></tr>'
    return "\n".join(
        "<tr>"
        f"<td>{escape(event.timestamp)}</td>"
        f"<td><span class=\"pill\">{escape(event.phase)}</span></td>"
        f"<td>{escape(event.message)}</td>"
        "</tr>"
        for event in job.events
    )


def _trace_rows(job: JobStatusResponse) -> str:
    if not job.decision_trace:
        return '<tr><td colspan="5">No decision trace recorded.</td></tr>'
    return "\n".join(
        "<tr>"
        f"<td>{escape(node.decision_id)}</td>"
        f"<td>{escape(node.agent_id)}</td>"
        f"<td>{escape(node.action)}</td>"
        f"<td>{escape(node.status)}</td>"
        f"<td>{escape(node.rationale)}</td>"
        "</tr>"
        for node in job.decision_trace
    )


def _ai_reflection(job: JobStatusResponse, pearson: str, rmse: str) -> str:
    risk_text = ", ".join(job.dataset_profile.risk_tags) if job.dataset_profile.risk_tags else "none"
    top = job.workflow_summary.top_candidates[0] if job.workflow_summary and job.workflow_summary.top_candidates else None
    top_text = f"{top.individual_id} ranked first with GEBV {top.gebv:.4f}" if top else "no candidate available"
    notes = [
        f"Decision confidence depends on data QC, validation design, and model metrics. Current risk tags: {risk_text}.",
        f"Primary result: {top_text}.",
        f"Metric review: Pearson r={pearson}; RMSE={rmse}. Compare these values with historical runs before deployment.",
        "Recommended next action: review top candidates with breeding constraints, population structure, and phenotype outlier diagnostics.",
    ]
    return "\n".join(f"<li>{escape(note)}</li>" for note in notes)


def _source_file_items(job: JobStatusResponse) -> str:
    if job.workflow_summary is None or not job.workflow_summary.source_files:
        return "<li>No source files recorded.</li>"
    return "\n".join(f"<li>{escape(path)}</li>" for path in job.workflow_summary.source_files)


def _snapshot_rows(
    *,
    job: JobStatusResponse,
    pearson: str,
    rmse: str,
    risk_text: str,
    fixed_effect_text: str,
) -> str:
    rows = [
        ("Trait", job.trait_name),
        ("Backend", job.workflow_backend or "unknown"),
        ("Population", job.task_understanding.population_description or "not specified"),
        ("Fixed effects", fixed_effect_text),
        ("Pearson r", pearson),
        ("RMSE", rmse),
        ("Risk tags", risk_text),
    ]
    return "\n".join(
        f"<div class=\"snapshot-row\"><span>{escape(label)}</span><strong>{escape(value)}</strong></div>"
        for label, value in rows
    )


def export_gs_html_report(
    *,
    job: JobStatusResponse,
    report_text: str,
    output_root: Path | None = None,
) -> PlotExportArtifact:
    if job.workflow_summary is None:
        raise ValueError("workflow summary is not available")

    out_dir = _report_output_dir(job, output_root) / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / "gs_report.html"

    candidates = job.workflow_summary.top_candidates
    top_candidate = candidates[0] if candidates else None
    metrics = job.workflow_summary.model_metrics
    risk_tags = job.dataset_profile.risk_tags
    fixed_effects = job.task_understanding.candidate_fixed_effects
    top_candidate_text = (
        f"{top_candidate.individual_id} / GEBV {top_candidate.gebv:.4f}"
        if top_candidate is not None
        else "No candidate"
    )
    risk_text = ", ".join(risk_tags) if risk_tags else "none"
    fixed_effect_text = ", ".join(fixed_effects) if fixed_effects else "none"
    pearson = _summary_stat(_metric(metrics, "metric::pearson", "预测准确度 r", "accuracy::pearson"))
    rmse = _summary_stat(_metric(metrics, "metric::rmse", "accuracy::rmse", "RMSE"))
    user_input = _first_user_input(job)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GS Agent Interface Visualization</title>
    <style>
        :root {{
            --primary-green: #2e7d32;
            --border-orange: #ef6c00;
            --bg-color: #ffffff;
            --text-color: #333333;
            --code-font: 'Courier New', Courier, monospace;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: white;
            color: var(--text-color);
            margin: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            align-items: baseline;
        }}

        .header h1 {{
            color: #d32f2f;
            margin: 0;
            font-size: 24px;
        }}

        .header h2 {{
            color: #d32f2f;
            margin: 0;
            font-size: 20px;
            font-weight: normal;
        }}

        .main-grid {{
            display: grid;
            grid-template-columns: 4fr 6fr;
            gap: 20px;
        }}

        .left-column, .right-column {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}

        .box {{
            border: 2px dashed var(--border-orange);
            border-radius: 15px;
            padding: 15px;
            background: #fff;
            position: relative;
        }}

        .box-title {{
            color: #000;
            font-weight: bold;
            margin-bottom: 10px;
            font-size: 16px;
        }}

        .section-header {{
            font-weight: bold;
            font-size: 18px;
            margin-bottom: 5px;
            color: #000;
        }}

        .user-input-content {{
            font-size: 14px;
            line-height: 1.5;
        }}

        .user-input-content strong {{
            color: var(--primary-green);
        }}

        .plan-content {{
            font-size: 14px;
            line-height: 1.6;
        }}

        .plan-step {{
            margin-bottom: 10px;
        }}

        .code-block {{
            font-family: var(--code-font);
            font-size: 12px;
            background-color: #fff;
            white-space: pre-wrap;
            line-height: 1.4;
        }}

        .comment {{ color: #888; }}
        .command {{ color: #000; }}
        .string {{ color: #a31515; }}
        .keyword {{ color: #0000ff; }}

        .log-output {{
            color: #666;
            margin-top: 10px;
            font-style: italic;
        }}

        .success-badge {{
            text-align: center;
            color: var(--primary-green);
            font-weight: bold;
            font-size: 14px;
            margin-top: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 5px;
        }}

        .success-badge::before {{
            content: "✓";
            display: inline-block;
            border: 2px solid var(--primary-green);
            border-radius: 50%;
            width: 16px;
            height: 16px;
            line-height: 16px;
            text-align: center;
            font-size: 12px;
        }}

        .results-table {{
            width: 100%;
            border-collapse: collapse;
            font-family: var(--code-font);
            font-size: 12px;
        }}

        .results-table th {{
            text-align: left;
            border-bottom: 1px solid #ccc;
            padding: 5px;
        }}

        .results-table td {{
            padding: 5px;
        }}

        .arrow-down {{
            text-align: center;
            color: var(--border-orange);
            font-size: 20px;
            margin: -15px 0;
            z-index: 1;
        }}

        @media (max-width: 900px) {{
            body {{ padding: 0 14px; }}
            .main-grid {{ grid-template-columns: 1fr; }}
            .header {{ flex-direction: column; gap: 4px; }}
        }}
    </style>
</head>
<body>

    <div class="header">
        <h1>GS Agent Analysis</h1>
        <h2>Case: Genomic Selection for {escape(job.trait_name)} in Animal Breeding Population</h2>
    </div>

    <div class="main-grid">
        <div class="left-column">
            <div>
                <div class="section-header">User's Inputs</div>
                <div class="box">
                    <div class="user-input-content">
                        <strong>Data and Description</strong><br>
                        • Genotype Data: <code>{escape(job.dataset_profile.genotype_path)}</code> (Format: {escape(job.dataset_profile.genotype_format or 'unknown')})<br>
                        • Phenotype Data: <code>{escape(job.dataset_profile.phenotype_path)}</code> (Trait: {escape(job.trait_name)})<br>
                        • Population: <em>{escape(job.task_understanding.population_description or 'animal breeding population')}</em><br>
                        • Workflow Backend: {escape(job.workflow_backend or 'native_nextflow')}<br>
                        <br>
                        <strong>Goal</strong><br>
                        {escape(user_input)}<br>
                        <br>
                        Perform Genomic Selection (GS) to estimate breeding values and identify top candidate individuals using the GS Agent pipeline.
                    </div>
                </div>
            </div>

            <div>
                <div class="section-header">Generated Codes and Code Execution by GS Agent</div>

                <div class="box">
                    <div class="box-title" style="color:var(--border-orange)"># Step 1: Data Contract and Quality Control</div>
                    <div class="code-block">
<span class="keyword">from</span> animal_gs_agent.services.dataset_profile_service <span class="keyword">import</span> build_dataset_profile
<span class="keyword">from</span> animal_gs_agent.schemas.jobs <span class="keyword">import</span> JobSubmissionRequest

<span class="comment"># Validate phenotype/genotype paths and trait column</span>
request = JobSubmissionRequest(
    user_message=<span class="string">"{escape(user_input)}"</span>,
    phenotype_path=<span class="string">"{escape(job.dataset_profile.phenotype_path)}"</span>,
    genotype_path=<span class="string">"{escape(job.dataset_profile.genotype_path)}"</span>,
    trait_name=<span class="string">"{escape(job.trait_name)}"</span>
)
dataset_profile = build_dataset_profile(request)
                    </div>
                    <div class="log-output">
[Log]<br>
Detected genotype format: {escape(job.dataset_profile.genotype_format or 'unknown')}<br>
Detected phenotype format: {escape(job.dataset_profile.phenotype_format or 'unknown')}<br>
Trait column present: {str(job.dataset_profile.trait_column_present)}<br>
Risk tags: {escape(risk_text)}
                    </div>
                    <div class="success-badge">Success</div>
                </div>

                <div class="arrow-down">↓</div>

                <div class="box">
                    <div class="box-title" style="color:var(--border-orange)"># Step 2: Model Planning and GBLUP Workflow</div>
                    <div class="code-block">
<span class="keyword">from</span> animal_gs_agent.services.workflow_service <span class="keyword">import</span> execute_fixed_workflow

<span class="comment"># Run fixed GS workflow with GBLUP-style candidate ranking</span>
job.workflow_result_dir = <span class="string">"{escape(job.workflow_result_dir or 'runs/' + job.job_id)}"</span>
workflow_result = execute_fixed_workflow(job)
                    </div>
                    <div class="log-output">
[Log]<br>
Backend: {escape(job.workflow_backend or 'native_nextflow')}<br>
Pearson r: {pearson}<br>
RMSE: {rmse}<br>
Source files: {escape(', '.join(job.workflow_summary.source_files[:2]) if job.workflow_summary.source_files else 'not recorded')}
                    </div>
                    <div class="success-badge">Success</div>
                </div>

                <div class="arrow-down">↓</div>

                <div class="box">
                    <div class="box-title" style="color:var(--border-orange)"># Step 3: Candidate Ranking and Report Export</div>
                    <div class="code-block">
<span class="keyword">from</span> animal_gs_agent.services.report_service <span class="keyword">import</span> build_job_report

<span class="comment"># Generate candidate decision report and AI interpretation</span>
report = build_job_report(job)

top_candidate = report.top_candidates[0]
html_report = report.html_report_artifact
                    </div>
                    <div class="log-output">
[Log]<br>
Total candidates: {job.workflow_summary.total_candidates}<br>
Top candidate: {escape(top_candidate_text)}<br>
HTML report: reports/gs_report.html<br>
Candidate table exported for breeding decision review.
                    </div>
                    <div class="success-badge">Success</div>
                </div>
            </div>
        </div>

        <div class="right-column">
            <div>
                <div class="section-header">Generated Plans by GS Agent</div>
                <div class="box">
                    <div class="plan-content">
                        <div class="plan-step">
                            <strong>Plan 1: Data Quality Control</strong><br>
                            First, I will inspect phenotype and genotype inputs, verify that the target trait <code>{escape(job.trait_name)}</code> exists in the phenotype table, and check whether blocking validation flags or QC risk tags are present.
                        </div>
                        <div class="plan-step">
                            <strong>Plan 2: Genomic Prediction Model</strong><br>
                            Next, I will use the fixed GS workflow to estimate genomic breeding values. The current model path is <code>GBLUP</code>-oriented, with fixed effects considered as: <code>{escape(fixed_effect_text)}</code>.
                        </div>
                        <div class="plan-step">
                            <strong>Plan 3: Candidate Selection</strong><br>
                            Finally, I will rank individuals by GEBV, summarize model metrics, and generate an AI-assisted interpretation for breeding personnel to review before deployment.
                        </div>
                    </div>
                </div>
            </div>

            <div>
                <div class="section-header">Processed Results by GS Agent</div>
                <div class="box">
                    <table class="results-table">
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>Individual_ID</th>
                                <th>GEBV</th>
                                <th>Decision Tag</th>
                                <th>Trait</th>
                                <th>Model</th>
                                <th>Priority</th>
                            </tr>
                        </thead>
                        <tbody>
                            {_candidate_rows_autogs(candidates, job.trait_name)}
                        </tbody>
                    </table>
                    <div style="margin-top: 15px; text-align: center;">
                        <div style="font-weight: bold; margin-bottom: 5px;">GEBV Ranking Preview</div>
                        {_gebv_preview_bars(candidates)}
                    </div>
                </div>
            </div>

            <div>
                <div class="section-header">Agent Feedback & Interpretation</div>
                <div class="box">
                    <div class="plan-content">
                         <strong>Interpretation of Results:</strong><br>
                         <p>{escape(report_text)}</p>
                         <p>The GS Agent completed a candidate-ranking task for <em>{escape(job.trait_name)}</em>. The leading recommendation is <strong>{escape(top_candidate_text)}</strong>. Model review metrics are Pearson r={pearson} and RMSE={rmse}; these should be compared against historical breeding records before final selection.</p>

                         <strong>Recommendations:</strong><br>
                         <ul style="margin: 5px 0 0 20px; padding: 0;">
                             <li>Prioritize the top-ranked candidates for breeder review and downstream validation.</li>
                             <li>Check population structure, phenotype outliers, and operational constraints before deployment.</li>
                             <li>Record accepted and rejected candidates as bad cases or validated cases for future agent memory.</li>
                         </ul>
                    </div>
                </div>
            </div>

        </div>
    </div>

</body>
</html>
"""
    html_path.write_text(html, encoding="utf-8")
    return PlotExportArtifact(format="html", artifact_path=str(html_path))
