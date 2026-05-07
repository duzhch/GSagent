"""Fixed GS workflow execution service."""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from animal_gs_agent.schemas.jobs import JobStatusResponse


@dataclass
class WorkflowExecutionResult:
    backend: str
    command: list[str]
    result_dir: str


class WorkflowExecutionError(Exception):
    """Raised when fixed workflow execution fails."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def build_native_nextflow_command(
    job: JobStatusResponse,
    pipeline_dir: Path,
    out_dir: Path,
) -> list[str]:
    return [
        "nextflow",
        "run",
        str(pipeline_dir / "main.nf"),
        "-profile",
        "local,native",
        "--genotype_vcf",
        job.dataset_profile.genotype_path,
        "--phenotype_csv",
        job.dataset_profile.phenotype_path,
        "--trait_name",
        job.trait_name,
        "--outdir",
        str(out_dir),
    ]


def execute_fixed_workflow(job: JobStatusResponse) -> WorkflowExecutionResult:
    pipeline_dir = Path(
        os.getenv(
            "ANIMAL_GS_AGENT_WORKFLOW_PIPELINE_DIR",
            "/work/home/zyqlab/dzhichao/Agent0428/gs_prototype/pipeline",
        )
    )
    output_root = Path(
        os.getenv(
            "ANIMAL_GS_AGENT_WORKFLOW_OUTPUT_ROOT",
            "/work/home/zyqlab/dzhichao/Agent0428/animal_gs_agent/runs",
        )
    )
    out_dir = output_root / job.job_id

    if not (pipeline_dir / "main.nf").exists():
        raise WorkflowExecutionError(
            code="workflow_pipeline_missing",
            message=f"main.nf not found in {pipeline_dir}",
        )

    if job.dataset_profile.genotype_format != "vcf":
        raise WorkflowExecutionError(
            code="workflow_input_invalid",
            message="native nextflow workflow requires genotype VCF input",
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    command = build_native_nextflow_command(job=job, pipeline_dir=pipeline_dir, out_dir=out_dir)
    completed = subprocess.run(
        command,
        cwd=str(pipeline_dir),
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.returncode != 0:
        stderr_tail = completed.stderr.strip().splitlines()[-1] if completed.stderr else ""
        raise WorkflowExecutionError(
            code="workflow_runtime_error",
            message=stderr_tail or f"workflow exited with code {completed.returncode}",
        )

    return WorkflowExecutionResult(
        backend="native_nextflow",
        command=command,
        result_dir=str(out_dir),
    )
