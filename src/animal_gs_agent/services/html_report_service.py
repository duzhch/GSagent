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

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GS Candidate Decision Report - {escape(job.trait_name)}</title>
  <style>
    :root {{
      --ink: #15202b;
      --muted: #53606f;
      --line: #d7dde4;
      --paper: #f6f2ea;
      --panel: #ffffff;
      --accent: #1f6f68;
      --accent-2: #c94f2d;
      --soft: #e7f1ef;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background:
        linear-gradient(135deg, rgba(31,111,104,.10), transparent 34%),
        linear-gradient(180deg, var(--paper), #ffffff 46%);
      font-family: "Aptos", "Segoe UI", sans-serif;
    }}
    .page {{
      width: min(1160px, calc(100% - 32px));
      margin: 0 auto;
      padding: 36px 0 56px;
    }}
    .cover {{
      display: grid;
      grid-template-columns: minmax(0, 1.45fr) minmax(280px, .55fr);
      gap: 24px;
      align-items: stretch;
      border-bottom: 3px solid var(--ink);
      padding-bottom: 28px;
    }}
    .cover-main {{
      min-height: 260px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .report-layout {{
      display: grid;
      grid-template-columns: minmax(240px, 300px) minmax(0, 1fr);
      gap: 18px;
      align-items: start;
      margin-top: 22px;
    }}
    .side-rail {{
      position: sticky;
      top: 18px;
      display: grid;
      gap: 14px;
    }}
    .rail-card {{
      background: #15202b;
      color: #f7fbfa;
      padding: 18px;
      border: 1px solid #15202b;
    }}
    .rail-card.light {{
      background: #fff;
      color: var(--ink);
      border-color: var(--line);
    }}
    .rail-card h2 {{
      margin: 0 0 14px;
      font-size: 17px;
    }}
    .snapshot-row {{
      display: grid;
      gap: 5px;
      padding: 10px 0;
      border-bottom: 1px solid rgba(255,255,255,.16);
    }}
    .rail-card.light .snapshot-row {{
      border-bottom-color: var(--line);
    }}
    .snapshot-row span {{
      color: #aebfbd;
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: .08em;
    }}
    .rail-card.light .snapshot-row span {{
      color: var(--muted);
    }}
    .snapshot-row strong {{
      font-size: 14px;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }}
    .source-list {{
      margin: 0;
      padding-left: 18px;
      color: var(--muted);
      line-height: 1.6;
      overflow-wrap: anywhere;
    }}
    .report-flow {{
      display: grid;
      gap: 16px;
    }}
    .section-block {{
      background: rgba(255,255,255,.86);
      border: 1px solid var(--line);
      padding: 22px;
    }}
    .section-kicker {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 14px;
      color: var(--accent-2);
      font-size: 13px;
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: .04em;
    }}
    .section-kicker::after {{
      content: "";
      height: 1px;
      flex: 1;
      background: var(--line);
    }}
    .section-title {{
      margin: 0 0 14px;
      font-size: 24px;
    }}
    .two-column {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
      align-items: stretch;
    }}
    .content-card {{
      background: #fff;
      border: 1px solid var(--line);
      padding: 16px;
    }}
    .content-card h3 {{
      margin: 0 0 10px;
      font-size: 16px;
    }}
    .timeline {{
      display: grid;
      gap: 10px;
      margin-top: 8px;
    }}
    .timeline-row {{
      display: grid;
      grid-template-columns: 170px 120px minmax(0, 1fr);
      gap: 12px;
      align-items: start;
      padding: 12px 0;
      border-bottom: 1px solid var(--line);
    }}
    .step-table td:first-child {{
      font-weight: 800;
      color: var(--accent);
    }}
    .recommendation-card {{
      background: var(--ink);
      color: white;
      padding: 22px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      min-height: 260px;
    }}
    .recommendation-card .label {{
      color: #b7c7c4;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: .08em;
      font-weight: 800;
    }}
    .recommendation-card .value {{
      margin-top: 16px;
      font-size: 32px;
      line-height: 1.08;
      font-weight: 900;
    }}
    .hero {{
      display: grid;
      grid-template-columns: 1.3fr .7fr;
      gap: 24px;
      align-items: stretch;
      border-bottom: 2px solid var(--ink);
      padding-bottom: 26px;
    }}
    .eyebrow {{
      margin: 0 0 10px;
      color: var(--accent-2);
      font-size: 13px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: .08em;
    }}
    h1 {{
      margin: 0;
      font-size: clamp(34px, 5vw, 64px);
      line-height: .95;
      letter-spacing: 0;
    }}
    h2 {{
      margin: 0 0 14px;
      font-size: 22px;
      letter-spacing: 0;
    }}
    .summary {{
      margin-top: 18px;
      color: var(--muted);
      max-width: 760px;
      font-size: 15px;
      line-height: 1.65;
      white-space: pre-wrap;
    }}
    .decision-card {{
      background: var(--ink);
      color: white;
      padding: 22px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      min-height: 230px;
    }}
    .decision-card .label {{
      color: #b7c7c4;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: .08em;
      font-weight: 800;
    }}
    .decision-card .value {{
      margin-top: 18px;
      font-size: 31px;
      line-height: 1.1;
      font-weight: 800;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin: 24px 0;
    }}
    .metric {{
      background: var(--panel);
      border: 1px solid var(--line);
      padding: 16px;
      min-height: 112px;
    }}
    .metric span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .08em;
      font-weight: 800;
    }}
    .metric strong {{
      display: block;
      margin-top: 13px;
      font-size: 24px;
    }}
    .section {{
      background: rgba(255,255,255,.78);
      border: 1px solid var(--line);
      margin-top: 18px;
      padding: 22px;
    }}
    .chart-shell {{
      overflow-x: auto;
      background: var(--soft);
      border: 1px solid #c8deda;
    }}
    svg {{
      min-width: 820px;
      width: 100%;
      height: auto;
      display: block;
      background: linear-gradient(90deg, #f4fbf9, #ffffff);
    }}
    .svg-title {{ font: 800 22px Aptos, Segoe UI, sans-serif; fill: var(--ink); }}
    .svg-label {{ font: 700 14px Aptos, Segoe UI, sans-serif; fill: var(--ink); }}
    .svg-score {{ font: 700 13px Aptos, Segoe UI, sans-serif; fill: var(--accent-2); }}
    .svg-bar {{ fill: var(--accent); }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: white;
      font-size: 14px;
    }}
    th, td {{
      text-align: left;
      padding: 12px 10px;
      border-bottom: 1px solid var(--line);
    }}
    th {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .08em;
    }}
    .audit {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
    }}
    .note {{
      background: #fff8ed;
      border-left: 4px solid var(--accent-2);
      padding: 14px 16px;
      color: #57321f;
      line-height: 1.55;
    }}
    .input-box {{
      background: #f1f6f5;
      border-left: 5px solid var(--accent);
      padding: 16px 18px;
      color: var(--ink);
      line-height: 1.65;
      font-weight: 650;
    }}
    .plan-list, .reflection-list {{
      margin: 0;
      padding-left: 20px;
      color: var(--ink);
      line-height: 1.7;
    }}
    .log-table {{
      margin-top: 8px;
    }}
    .pill {{
      display: inline-block;
      padding: 4px 8px;
      border: 1px solid #bdd5d1;
      background: #edf7f5;
      color: var(--accent);
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
    }}
    .result-block {{
      margin-top: 18px;
    }}
    @media (max-width: 820px) {{
      .cover, .hero, .audit, .report-layout, .two-column {{ grid-template-columns: 1fr; }}
      .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .side-rail {{ position: static; }}
      .timeline-row {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 520px) {{
      .page {{ width: min(100% - 20px, 1160px); padding-top: 22px; }}
      .grid {{ grid-template-columns: 1fr; }}
      .section, .decision-card {{ padding: 16px; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="cover">
      <div class="cover-main">
        <p class="eyebrow">Genomic Selection Harness</p>
        <h1>GS Candidate Decision Report</h1>
        <p class="summary">{escape(report_text)}</p>
        <div class="grid" aria-label="Executive summary">
          <div class="metric"><span>Total candidates</span><strong>{job.workflow_summary.total_candidates}</strong></div>
          <div class="metric"><span>Pearson r</span><strong>{pearson}</strong></div>
          <div class="metric"><span>RMSE</span><strong>{rmse}</strong></div>
          <div class="metric"><span>Risk tags</span><strong>{escape(risk_text)}</strong></div>
        </div>
      </div>
      <aside class="recommendation-card">
        <div>
          <div class="label">Candidate Recommendation</div>
          <div class="value">{escape(top_candidate_text)}</div>
        </div>
        <div>
          <div class="label">Trait</div>
          <div>{escape(job.trait_name)}</div>
        </div>
      </aside>
    </section>

    <section class="report-layout">
      <aside class="side-rail">
        <div class="rail-card">
          <h2>Model & Data Snapshot</h2>
          {_snapshot_rows(job=job, pearson=pearson, rmse=rmse, risk_text=risk_text, fixed_effect_text=fixed_effect_text)}
        </div>
        <div class="rail-card light">
          <h2>Source Files</h2>
          <ul class="source-list">
            {_source_file_items(job)}
          </ul>
        </div>
      </aside>

      <div class="report-flow">
        <section class="section-block">
          <div class="section-kicker">01 用户输入 / User Input</div>
          <h2 class="section-title">Input Prompt</h2>
          <div class="input-box">{escape(user_input)}</div>
        </section>

        <section class="section-block">
          <div class="section-kicker">02 AI 任务规划 / AI Task Plan</div>
          <h2 class="section-title">Agent Planning Board</h2>
          <div class="two-column">
            <div class="content-card">
              <h3>Task decomposition</h3>
              <ul class="plan-list">
                {_plan_items(job)}
              </ul>
            </div>
            <div class="content-card">
              <h3>Execution assumption</h3>
              <ul class="reflection-list">
                <li>Use structured task understanding to map user intent to a GS ranking task.</li>
                <li>Keep numerical estimation inside the fixed workflow and use AI for planning, explanation, and audit context.</li>
                <li>Return candidate individuals as the primary actionable output.</li>
              </ul>
            </div>
          </div>
        </section>

        <section class="section-block">
          <div class="section-kicker">03 执行日志 / Execution Log</div>
          <h2 class="section-title">Run Timeline</h2>
          <table class="log-table">
            <thead>
              <tr><th>Time</th><th>Phase</th><th>Message</th></tr>
            </thead>
            <tbody>
              {_event_rows(job)}
            </tbody>
          </table>
        </section>

        <section class="section-block">
          <div class="section-kicker">04 执行步骤 / Execution Steps</div>
          <h2 class="section-title">Step Evidence</h2>
          <table class="step-table">
            <thead>
              <tr><th>Decision ID</th><th>Agent</th><th>Action</th><th>Status</th><th>Rationale</th></tr>
            </thead>
            <tbody>
              {_trace_rows(job)}
            </tbody>
          </table>
        </section>

        <section class="section-block">
          <div class="section-kicker">05 GS 结果 / GS Results</div>
          <h2 class="section-title">Candidate Ranking and Selection Table</h2>
          <div class="result-block">
            <h2>Candidate GEBV Ranking</h2>
            <div class="chart-shell">{_candidate_svg(candidates)}</div>
          </div>
          <div class="result-block">
            <h2>Candidate Individuals</h2>
            <table>
              <thead>
                <tr><th>Rank</th><th>Individual ID</th><th>GEBV</th><th>Decision tag</th></tr>
              </thead>
              <tbody>
                {_candidate_rows(candidates)}
              </tbody>
            </table>
          </div>
        </section>

        <section class="section-block">
          <div class="section-kicker">06 AI 反思 / AI Reflection</div>
          <h2 class="section-title">Decision Review</h2>
          <div class="two-column">
            <div class="content-card">
              <h3>Reflection</h3>
              <ul class="reflection-list">
                {_ai_reflection(job, pearson, rmse)}
              </ul>
            </div>
            <div class="content-card">
              <h3>Audit context</h3>
              <p class="summary">Fixed effects considered: {escape(fixed_effect_text)}. Workflow backend: {escape(job.workflow_backend or "unknown")}.</p>
              <p class="summary">Review population structure, phenotype outliers, leakage risk, and business constraints before final breeding deployment.</p>
            </div>
          </div>
        </section>
      </div>
    </section>
  </main>
</body>
</html>
"""
    html_path.write_text(html, encoding="utf-8")
    return PlotExportArtifact(format="html", artifact_path=str(html_path))
