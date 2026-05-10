from animal_gs_agent.schemas.dataset_profile import DatasetPathChecks, DatasetProfile
from animal_gs_agent.schemas.jobs import JobStatusResponse
from animal_gs_agent.schemas.task_understanding import TaskUnderstandingResult
from animal_gs_agent.services.workflow_service import (
    WorkflowExecutionError,
    _is_login_node,
    build_native_nextflow_command,
    execute_fixed_workflow,
)


def _build_job(phenotype_path: str, genotype_path: str, trait_name: str = "daily_gain") -> JobStatusResponse:
    return JobStatusResponse(
        job_id="job12345",
        status="queued",
        trait_name=trait_name,
        task_understanding=TaskUnderstandingResult(
            request_scope="supported_gs",
            trait_name=trait_name,
            user_goal="rank candidates",
            candidate_fixed_effects=["sex"],
            population_description="pig",
            missing_inputs=[],
            confidence=0.9,
            clarification_needed=False,
        ),
        dataset_profile=DatasetProfile(
            phenotype_path=phenotype_path,
            genotype_path=genotype_path,
            path_checks=DatasetPathChecks(phenotype_exists=True, genotype_exists=True),
            phenotype_format="csv",
            genotype_format="vcf",
            phenotype_headers=["animal_id", trait_name],
            trait_column_present=True,
            validation_flags=[],
        ),
    )


def test_build_native_nextflow_command_contains_fixed_workflow_args(tmp_path) -> None:
    pipeline_dir = tmp_path / "pipeline"
    pipeline_dir.mkdir()
    out_dir = tmp_path / "runs" / "job12345"

    job = _build_job(
        phenotype_path=str(tmp_path / "pheno.csv"),
        genotype_path=str(tmp_path / "geno.vcf"),
    )

    command = build_native_nextflow_command(job=job, pipeline_dir=pipeline_dir, out_dir=out_dir)

    assert command[:4] == ["nextflow", "run", str(pipeline_dir / "main.nf"), "-profile"]
    assert "local,native" in command
    assert "--genotype_vcf" in command
    assert "--phenotype_csv" in command
    assert "--trait_name" in command
    assert "--outdir" in command


def test_execute_fixed_workflow_raises_when_pipeline_missing(tmp_path, monkeypatch) -> None:
    pipeline_dir = tmp_path / "pipeline"
    pipeline_dir.mkdir()

    job = _build_job(
        phenotype_path=str(tmp_path / "pheno.csv"),
        genotype_path=str(tmp_path / "geno.vcf"),
    )

    monkeypatch.setenv("ANIMAL_GS_AGENT_WORKFLOW_PIPELINE_DIR", str(pipeline_dir))
    monkeypatch.setenv("ANIMAL_GS_AGENT_WORKFLOW_OUTPUT_ROOT", str(tmp_path / "runs"))

    try:
        execute_fixed_workflow(job)
    except WorkflowExecutionError as exc:
        assert exc.code == "workflow_pipeline_missing"
    else:
        raise AssertionError("expected WorkflowExecutionError")


def test_execute_fixed_workflow_submits_slurm_on_login_node_in_auto_mode(tmp_path, monkeypatch) -> None:
    pipeline_dir = tmp_path / "pipeline"
    pipeline_dir.mkdir()
    (pipeline_dir / "main.nf").write_text("workflow {}", encoding="utf-8")

    submit_script = tmp_path / "submit.sh"
    submit_script.write_text("#!/usr/bin/env bash\necho submit\n", encoding="utf-8")

    job = _build_job(
        phenotype_path=str(tmp_path / "pheno.csv"),
        genotype_path=str(tmp_path / "geno.vcf"),
    )

    monkeypatch.setenv("ANIMAL_GS_AGENT_WORKFLOW_PIPELINE_DIR", str(pipeline_dir))
    monkeypatch.setenv("ANIMAL_GS_AGENT_WORKFLOW_OUTPUT_ROOT", str(tmp_path / "runs"))
    monkeypatch.setenv("ANIMAL_GS_AGENT_WORKFLOW_EXECUTION_POLICY", "auto")
    monkeypatch.setenv("ANIMAL_GS_AGENT_FORCE_LOGIN_NODE", "1")
    monkeypatch.setenv("ANIMAL_GS_AGENT_SLURM_SUBMIT_SCRIPT", str(submit_script))

    call_args = {"command": None}

    class _Completed:
        returncode = 0
        stdout = "123456\n"
        stderr = ""

    def _fake_run(command, *args, **kwargs):
        call_args["command"] = command
        return _Completed()

    monkeypatch.setattr("animal_gs_agent.services.workflow_service.subprocess.run", _fake_run)

    result = execute_fixed_workflow(job)

    assert result.backend == "slurm_nextflow_submit"
    assert result.status == "submitted"
    assert result.submission_id == "123456"
    assert call_args["command"] is not None
    assert call_args["command"][:3] == ["sbatch", "--parsable", "--export"]
    export_arg = call_args["command"][3]
    assert export_arg.startswith("ALL,")
    assert "ANIMAL_GS_AGENT_JOB_ID=job12345" in export_arg
    assert f"ANIMAL_GS_AGENT_TRAIT_NAME={job.trait_name}" in export_arg
    assert f"ANIMAL_GS_AGENT_GENOTYPE_VCF={job.dataset_profile.genotype_path}" in export_arg
    assert f"ANIMAL_GS_AGENT_PHENOTYPE_CSV={job.dataset_profile.phenotype_path}" in export_arg


def test_execute_fixed_workflow_raises_when_login_node_without_submit_script(tmp_path, monkeypatch) -> None:
    pipeline_dir = tmp_path / "pipeline"
    pipeline_dir.mkdir()
    (pipeline_dir / "main.nf").write_text("workflow {}", encoding="utf-8")

    job = _build_job(
        phenotype_path=str(tmp_path / "pheno.csv"),
        genotype_path=str(tmp_path / "geno.vcf"),
    )

    monkeypatch.setenv("ANIMAL_GS_AGENT_WORKFLOW_PIPELINE_DIR", str(pipeline_dir))
    monkeypatch.setenv("ANIMAL_GS_AGENT_WORKFLOW_OUTPUT_ROOT", str(tmp_path / "runs"))
    monkeypatch.setenv("ANIMAL_GS_AGENT_WORKFLOW_EXECUTION_POLICY", "auto")
    monkeypatch.setenv("ANIMAL_GS_AGENT_FORCE_LOGIN_NODE", "1")
    monkeypatch.delenv("ANIMAL_GS_AGENT_SLURM_SUBMIT_SCRIPT", raising=False)

    try:
        execute_fixed_workflow(job)
    except WorkflowExecutionError as exc:
        assert exc.code == "workflow_slurm_submit_script_missing"
    else:
        raise AssertionError("expected WorkflowExecutionError")


def test_is_login_node_returns_true_when_sbatch_present_without_active_job(monkeypatch) -> None:
    monkeypatch.delenv("ANIMAL_GS_AGENT_FORCE_LOGIN_NODE", raising=False)
    monkeypatch.delenv("SLURM_JOB_ID", raising=False)
    monkeypatch.setattr("animal_gs_agent.services.workflow_service.socket.gethostname", lambda: "r03c03n07")
    monkeypatch.setattr("animal_gs_agent.services.workflow_service.shutil.which", lambda cmd: "/usr/bin/sbatch")

    assert _is_login_node() is True


def test_is_login_node_returns_false_inside_slurm_allocation(monkeypatch) -> None:
    monkeypatch.delenv("ANIMAL_GS_AGENT_FORCE_LOGIN_NODE", raising=False)
    monkeypatch.setenv("SLURM_JOB_ID", "12345")
    monkeypatch.setattr("animal_gs_agent.services.workflow_service.socket.gethostname", lambda: "login01")
    monkeypatch.setattr("animal_gs_agent.services.workflow_service.shutil.which", lambda cmd: "/usr/bin/sbatch")

    assert _is_login_node() is False
