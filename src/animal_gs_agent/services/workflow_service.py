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
    genotype_vcf_path: str | None = None,
) -> list[str]:
    return [
        "nextflow",
        "run",
        str(pipeline_dir / "main.nf"),
        "-profile",
        "local,native",
        "--genotype_vcf",
        genotype_vcf_path or job.dataset_profile.genotype_path,
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


def _resolve_genotype_vcf(job: JobStatusResponse, out_dir: Path) -> str:
    genotype_format = (job.dataset_profile.genotype_format or "").lower()
    if genotype_format == "vcf":
        return job.dataset_profile.genotype_path
    if genotype_format != "bed":
        raise WorkflowExecutionError(
            code="workflow_input_invalid",
            message="workflow only supports genotype format vcf or bed",
        )

    bed_path = Path(job.dataset_profile.genotype_path).expanduser().resolve()
    if bed_path.suffix.lower() != ".bed":
        raise WorkflowExecutionError(
            code="workflow_input_invalid",
            message="bed genotype input must end with .bed",
        )

    prefix = bed_path.with_suffix("")
    required = [bed_path, prefix.with_suffix(".bim"), prefix.with_suffix(".fam")]
    missing = [path for path in required if not path.exists()]
    if missing:
        raise WorkflowExecutionError(
            code="workflow_input_invalid",
            message=f"bed input is incomplete, missing: {', '.join(str(path) for path in missing)}",
        )

    if shutil.which("plink2") is None:
        raise WorkflowExecutionError(
            code="workflow_dependency_missing",
            message="plink2 is required to convert BED input to VCF",
        )

    converted_prefix = out_dir / "inputs" / "genotype_from_bed"
    converted_prefix.parent.mkdir(parents=True, exist_ok=True)
    convert_command = [
        "plink2",
        "--bfile",
        str(prefix),
        "--recode",
        "vcf",
        "--out",
        str(converted_prefix),
    ]
    converted = subprocess.run(
        convert_command,
        capture_output=True,
        text=True,
        check=False,
    )
    if converted.returncode != 0:
        raise WorkflowExecutionError(
            code="workflow_bed_to_vcf_failed",
            message=converted.stderr.strip() or "plink2 BED->VCF conversion failed",
        )

    vcf_path = Path(f"{converted_prefix}.vcf")
    if not vcf_path.exists():
        raise WorkflowExecutionError(
            code="workflow_bed_to_vcf_failed",
            message=f"plink2 conversion did not produce VCF: {vcf_path}",
        )
    return str(vcf_path)


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

    out_dir.mkdir(parents=True, exist_ok=True)
    genotype_vcf_path = _resolve_genotype_vcf(job=job, out_dir=out_dir)

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
                f"ANIMAL_GS_AGENT_GENOTYPE_VCF={genotype_vcf_path}",
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

    command = build_native_nextflow_command(
        job=job,
        pipeline_dir=pipeline_dir,
        out_dir=out_dir,
        genotype_vcf_path=genotype_vcf_path,
    )
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
