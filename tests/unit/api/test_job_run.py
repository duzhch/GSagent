from fastapi.testclient import TestClient

from animal_gs_agent.api.app import create_app
from animal_gs_agent.services.workflow_service import WorkflowExecutionError, WorkflowExecutionResult


def _patch_llm(monkeypatch) -> None:
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_API_KEY", "secret-key")
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_MODEL", "deepseek-chat")

    def fake_request_json(self, system_prompt: str, user_prompt: str) -> dict:
        return {
            "request_scope": "supported_gs",
            "trait_name": "daily_gain",
            "user_goal": "rank candidates for genomic selection",
            "candidate_fixed_effects": ["sex", "batch"],
            "population_description": "commercial pig population",
            "missing_inputs": [],
            "confidence": 0.91,
            "clarification_needed": False,
        }

    monkeypatch.setattr(
        "animal_gs_agent.llm.client.OpenAICompatibleLLMClient.request_json",
        fake_request_json,
    )


def test_run_job_transitions_to_completed_for_valid_dataset(monkeypatch, tmp_path) -> None:
    _patch_llm(monkeypatch)

    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text("animal_id,daily_gain,sex\nA1,1.2,M\n", encoding="utf-8")

    genotype_file = tmp_path / "geno.pgen"
    genotype_file.write_text("placeholder", encoding="utf-8")

    client = TestClient(create_app())
    submit_response = client.post(
        "/jobs",
        json={
            "user_message": "Run genomic selection for daily_gain",
            "trait_name": "daily_gain",
            "phenotype_path": str(phenotype_file),
            "genotype_path": str(genotype_file),
        },
    )
    job_id = submit_response.json()["job_id"]

    def fake_execute_workflow(job):
        return WorkflowExecutionResult(
            backend="native_nextflow",
            command=["nextflow", "run", "main.nf"],
            result_dir=f"/tmp/{job.job_id}",
        )

    monkeypatch.setattr(
        "animal_gs_agent.api.routes.jobs.execute_fixed_workflow",
        fake_execute_workflow,
    )

    run_response = client.post(f"/jobs/{job_id}/run")

    assert run_response.status_code == 200
    assert run_response.json()["status"] == "completed"
    assert run_response.json()["workflow_backend"] == "native_nextflow"


def test_run_job_transitions_to_failed_when_trait_missing(monkeypatch, tmp_path) -> None:
    _patch_llm(monkeypatch)

    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text("animal_id,sex\nA1,M\n", encoding="utf-8")

    genotype_file = tmp_path / "geno.pgen"
    genotype_file.write_text("placeholder", encoding="utf-8")

    client = TestClient(create_app())
    submit_response = client.post(
        "/jobs",
        json={
            "user_message": "Run genomic selection for daily_gain",
            "trait_name": "daily_gain",
            "phenotype_path": str(phenotype_file),
            "genotype_path": str(genotype_file),
        },
    )
    job_id = submit_response.json()["job_id"]

    run_response = client.post(f"/jobs/{job_id}/run")

    body = run_response.json()

    assert run_response.status_code == 200
    assert body["status"] == "failed"
    assert body["execution_error"] == "trait_column_missing"


def test_run_job_transitions_to_failed_when_workflow_runtime_errors(monkeypatch, tmp_path) -> None:
    _patch_llm(monkeypatch)

    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text("animal_id,daily_gain,sex\nA1,1.2,M\n", encoding="utf-8")

    genotype_file = tmp_path / "geno.vcf"
    genotype_file.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")

    client = TestClient(create_app())
    submit_response = client.post(
        "/jobs",
        json={
            "user_message": "Run genomic selection for daily_gain",
            "trait_name": "daily_gain",
            "phenotype_path": str(phenotype_file),
            "genotype_path": str(genotype_file),
        },
    )
    job_id = submit_response.json()["job_id"]

    def fake_execute_workflow(job):
        raise WorkflowExecutionError(
            code="workflow_runtime_error",
            message="nextflow failed with exit code 1",
        )

    monkeypatch.setattr(
        "animal_gs_agent.api.routes.jobs.execute_fixed_workflow",
        fake_execute_workflow,
    )

    run_response = client.post(f"/jobs/{job_id}/run")
    body = run_response.json()

    assert run_response.status_code == 200
    assert body["status"] == "failed"
    assert body["execution_error"] == "workflow_runtime_error"
