from fastapi.testclient import TestClient

from animal_gs_agent.api.app import create_app
from animal_gs_agent.schemas.jobs import RankedCandidate, WorkflowSummary
from animal_gs_agent.services.workflow_service import WorkflowExecutionResult


def test_get_job_returns_submitted_job_status(monkeypatch) -> None:
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

    client = TestClient(create_app())

    submit_response = client.post(
        "/jobs",
        json={
            "user_message": "Run genomic selection for daily_gain",
            "trait_name": "daily_gain",
            "phenotype_path": "data/demo/phenotypes.csv",
            "genotype_path": "data/demo/genotypes.pgen",
        },
    )
    job_id = submit_response.json()["job_id"]

    response = client.get(f"/jobs/{job_id}")

    body = response.json()

    assert response.status_code == 200
    assert body["job_id"] == job_id
    assert body["status"] == "queued"
    assert body["trait_name"] == "daily_gain"
    assert body["task_understanding"]["request_scope"] == "supported_gs"
    assert body["dataset_profile"]["phenotype_format"] == "csv"
    assert body["dataset_profile"]["genotype_format"] == "pgen"
    assert body["dataset_profile"]["validation_flags"] == [
        "phenotype_not_found",
        "genotype_not_found",
    ]
    assert body["events"][0]["phase"] == "queued"


def test_get_job_refreshes_slurm_submitted_job_to_completed(monkeypatch, tmp_path) -> None:
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

    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text("animal_id,daily_gain,sex\nA1,1.2,M\n", encoding="utf-8")
    genotype_file = tmp_path / "geno.vcf"
    genotype_file.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")
    result_dir = tmp_path / "run_result"
    (result_dir / "gblup").mkdir(parents=True)

    def fake_execute_workflow(job):
        return WorkflowExecutionResult(
            backend="slurm_nextflow_submit",
            command=["sbatch", "submit.sh"],
            result_dir=str(result_dir),
            status="submitted",
            submission_id="123456",
        )

    monkeypatch.setattr(
        "animal_gs_agent.api.routes.jobs.execute_fixed_workflow",
        fake_execute_workflow,
    )
    monkeypatch.setattr(
        "animal_gs_agent.api.routes.jobs.poll_slurm_job_state",
        lambda submission_id: "COMPLETED",
    )
    monkeypatch.setattr(
        "animal_gs_agent.api.routes.jobs.parse_workflow_outputs",
        lambda result_dir, trait_name, top_n=10: WorkflowSummary(
            trait_name=trait_name,
            total_candidates=1,
            top_candidates=[RankedCandidate(individual_id="A1", gebv=1.0, rank=1)],
            model_metrics={},
            source_files=[],
        ),
    )

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
    assert run_response.status_code == 200
    assert run_response.json()["status"] == "running"

    status_response = client.get(f"/jobs/{job_id}")
    body = status_response.json()

    assert status_response.status_code == 200
    assert body["status"] == "completed"
    assert body["workflow_submission_id"] == "123456"
