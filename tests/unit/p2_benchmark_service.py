from pathlib import Path

from animal_gs_agent.schemas.dataset_profile import DatasetPathChecks, DatasetProfile
from animal_gs_agent.schemas.jobs import JobStatusResponse, RankedCandidate, WorkflowSummary
from animal_gs_agent.schemas.task_understanding import TaskUnderstandingResult
from animal_gs_agent.services.benchmark_service import (
    build_ablation_benchmark,
    build_baseline_benchmark,
    export_plot_artifact,
)


def _job() -> JobStatusResponse:
    return JobStatusResponse(
        job_id="bench001",
        status="completed",
        trait_name="daily_gain",
        task_understanding=TaskUnderstandingResult(
            request_scope="supported_gs",
            trait_name="daily_gain",
            user_goal="rank candidates",
            candidate_fixed_effects=["sex"],
            population_description="pig",
            missing_inputs=[],
            confidence=0.91,
            clarification_needed=False,
        ),
        dataset_profile=DatasetProfile(
            phenotype_path="/tmp/pheno.csv",
            genotype_path="/tmp/geno.vcf",
            path_checks=DatasetPathChecks(phenotype_exists=True, genotype_exists=True),
            phenotype_format="csv",
            genotype_format="vcf",
            phenotype_headers=["animal_id", "daily_gain"],
            trait_column_present=True,
            validation_flags=[],
        ),
        workflow_summary=WorkflowSummary(
            trait_name="daily_gain",
            total_candidates=2,
            top_candidates=[
                RankedCandidate(individual_id="A1", gebv=1.20, rank=1),
                RankedCandidate(individual_id="A2", gebv=1.05, rank=2),
            ],
            model_metrics={"metric::pearson": "0.73", "metric::rmse": "0.17"},
            source_files=["gblup/gebv_predictions.csv"],
        ),
    )


def test_baseline_benchmark_compares_single_react_and_multi_agent() -> None:
    report = build_baseline_benchmark(job=_job(), random_seed=42)

    arm_ids = {item.arm_id for item in report.compared_arms}
    assert arm_ids == {"single_agent", "react_agent", "multi_agent"}
    assert report.winner_arm_id in arm_ids
    assert report.reproducibility_tag.startswith("seed=42")


def test_ablation_benchmark_outputs_delta_effects() -> None:
    baseline = build_baseline_benchmark(job=_job(), random_seed=7)
    ablations = build_ablation_benchmark(baseline_report=baseline)

    assert len(ablations) >= 2
    assert all(item.ablation_name for item in ablations)
    assert any(item.impact_label in {"minor", "moderate", "major"} for item in ablations)


def test_plot_export_writes_csv_artifact(tmp_path) -> None:
    baseline = build_baseline_benchmark(job=_job(), random_seed=7)
    ablations = build_ablation_benchmark(baseline_report=baseline)
    artifact = export_plot_artifact(
        job_id="bench001",
        baseline_report=baseline,
        ablation_report=ablations,
        output_root=Path(tmp_path),
    )

    assert artifact.format == "csv"
    assert artifact.artifact_path.endswith(".csv")
    assert Path(artifact.artifact_path).exists() is True
