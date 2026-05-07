"""Workflow output parsing helpers."""

from __future__ import annotations

import csv
from pathlib import Path

from animal_gs_agent.schemas.jobs import RankedCandidate, WorkflowSummary


def _parse_model_summary(path: Path) -> dict[str, str]:
    metrics: dict[str, str] = {}
    if not path.exists():
        return metrics

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key and value:
            metrics[key] = value
    return metrics


def parse_workflow_outputs(result_dir: Path | str, trait_name: str, top_n: int = 10) -> WorkflowSummary:
    root = Path(result_dir)
    gblup_dir = root / "gblup"
    gebv_path = gblup_dir / "gebv_predictions.csv"
    model_summary_path = gblup_dir / "model_summary.txt"
    if not gebv_path.exists():
        raise FileNotFoundError(f"missing workflow output: {gebv_path}")

    candidates: list[RankedCandidate] = []
    with gebv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            individual_id = (row.get("individual_id") or "").strip()
            if not individual_id:
                continue
            rank_raw = (row.get("gebv_rank") or "").strip()
            gebv_raw = (row.get("gebv") or "").strip()
            if not rank_raw or not gebv_raw:
                continue
            candidates.append(
                RankedCandidate(
                    individual_id=individual_id,
                    gebv=float(gebv_raw),
                    rank=int(float(rank_raw)),
                )
            )

    candidates.sort(key=lambda item: item.rank)
    metrics = _parse_model_summary(model_summary_path)

    source_files = ["gblup/gebv_predictions.csv"]
    if model_summary_path.exists():
        source_files.append("gblup/model_summary.txt")

    return WorkflowSummary(
        trait_name=trait_name,
        total_candidates=len(candidates),
        top_candidates=candidates[:top_n],
        model_metrics=metrics,
        source_files=source_files,
    )
