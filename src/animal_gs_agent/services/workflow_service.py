"""Fixed GS workflow execution service."""

import os
import shutil
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from animal_gs_agent.schemas.jobs import JobStatusResponse


@dataclass
class WorkflowExecutionResult:
    backend: str
    command: list[str]
    result_dir: str
    status: Literal["completed", "submitted"] = "completed"
    submission_id: str | None = None


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


def _is_login_node() -> bool:
    forced = os.getenv("ANIMAL_GS_AGENT_FORCE_LOGIN_NODE", "").strip().lower()
    if forced in {"1", "true", "yes"}:
        return True
    if os.getenv("SLURM_JOB_ID"):
        return False

    hostname = socket.gethostname().lower()
    if any(token in hostname for token in ("login", "head", "front", "submit", "mgmt")):
        return True

    prefer_slurm = os.getenv("ANIMAL_GS_AGENT_AUTO_PREFER_SLURM", "1").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    return prefer_slurm and shutil.which("sbatch") is not None


def _default_pipeline_dir() -> Path:
    workdir = Path(os.getenv("ANIMAL_GS_AGENT_WORKDIR", os.getcwd())).expanduser().resolve()
    return workdir / "pipeline"


def _default_output_root() -> Path:
    workdir = Path(os.getenv("ANIMAL_GS_AGENT_WORKDIR", os.getcwd())).expanduser().resolve()
    return workdir / "runs"


def execute_fixed_workflow(job: JobStatusResponse) -> WorkflowExecutionResult:
    pipeline_dir = Path(
        os.getenv(
            "ANIMAL_GS_AGENT_WORKFLOW_PIPELINE_DIR",
            str(_default_pipeline_dir()),
        )
    )
    output_root = Path(
        os.getenv(
            "ANIMAL_GS_AGENT_WORKFLOW_OUTPUT_ROOT",
            str(_default_output_root()),
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

    execution_policy = os.getenv("ANIMAL_GS_AGENT_WORKFLOW_EXECUTION_POLICY", "auto").strip().lower()
    if execution_policy not in {"auto", "local", "slurm"}:
        raise WorkflowExecutionError(
            code="workflow_execution_policy_invalid",
            message=f"unsupported execution policy: {execution_policy}",
        )

    should_submit_slurm = execution_policy == "slurm" or (
        execution_policy == "auto" and _is_login_node()
    )
    if should_submit_slurm:
        submit_script = os.getenv("ANIMAL_GS_AGENT_SLURM_SUBMIT_SCRIPT")
        if not submit_script or not Path(submit_script).exists():
            raise WorkflowExecutionError(
                code="workflow_slurm_submit_script_missing",
                message="slurm submit script is not configured",
            )

        submit_exports = ",".join(
            [
                "ALL",
                f"ANIMAL_GS_AGENT_JOB_ID={job.job_id}",
                f"ANIMAL_GS_AGENT_TRAIT_NAME={job.trait_name}",
                f"ANIMAL_GS_AGENT_GENOTYPE_VCF={job.dataset_profile.genotype_path}",
                f"ANIMAL_GS_AGENT_PHENOTYPE_CSV={job.dataset_profile.phenotype_path}",
                f"ANIMAL_GS_AGENT_OUTPUT_DIR={out_dir}",
                f"ANIMAL_GS_AGENT_PIPELINE_DIR={pipeline_dir}",
            ]
        )
        submit_command = ["sbatch", "--parsable", "--export", submit_exports, submit_script]
        submitted = subprocess.run(
            submit_command,
            capture_output=True,
            text=True,
            check=False,
        )
        if submitted.returncode != 0:
            raise WorkflowExecutionError(
                code="workflow_slurm_submit_failed",
                message=submitted.stderr.strip() or "sbatch submission failed",
            )

        submission_id = submitted.stdout.strip().split(";")[0]
        return WorkflowExecutionResult(
            backend="slurm_nextflow_submit",
            command=submit_command,
            result_dir=str(out_dir),
            status="submitted",
            submission_id=submission_id or None,
        )

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
        status="completed",
    )
