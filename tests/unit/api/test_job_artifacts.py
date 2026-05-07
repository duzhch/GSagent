from fastapi.testclient import TestClient

from animal_gs_agent.api.app import create_app
from animal_gs_agent.schemas.jobs import RankedCandidate, WorkflowSummary
from animal_gs_agent.services.workflow_service import WorkflowExecutionResult


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


def test_job_artifacts_returns_workflow_outputs(monkeypatch, tmp_path) -> None:
    _patch_llm(monkeypatch)

    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text("animal_id,daily_gain,sex\nA1,1.2,M\n", encoding="utf-8")
    genotype_file = tmp_path / "geno.vcf"
    genotype_file.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")

    result_dir = tmp_path / "run_result"
    (result_dir / "gblup").mkdir(parents=True)
    (result_dir / "gblup" / "gebv_predictions.csv").write_text("id,gebv\n", encoding="utf-8")
    (result_dir / "gblup" / "model_summary.txt").write_text("h²: 0.42\n", encoding="utf-8")

    def fake_execute_workflow(job):
        return WorkflowExecutionResult(
            backend="native_nextflow",
            command=["nextflow", "run", "main.nf"],
            result_dir=str(result_dir),
        )

    def fake_parse_outputs(result_dir, trait_name, top_n=10):
        return WorkflowSummary(
            trait_name=trait_name,
            total_candidates=1,
            top_candidates=[RankedCandidate(individual_id="A1001", gebv=1.2345, rank=1)],
            model_metrics={"h²": "0.42"},
            source_files=["gblup/gebv_predictions.csv", "gblup/model_summary.txt"],
        )

    monkeypatch.setattr("animal_gs_agent.api.routes.jobs.execute_fixed_workflow", fake_execute_workflow)
    monkeypatch.setattr("animal_gs_agent.api.routes.jobs.parse_workflow_outputs", fake_parse_outputs)

    client = TestClient(create_app())
    submit = client.post(
        "/jobs",
        json={
            "user_message": "Run genomic selection for daily_gain",
            "trait_name": "daily_gain",
            "phenotype_path": str(phenotype_file),
            "genotype_path": str(genotype_file),
        },
    )
    job_id = submit.json()["job_id"]

    run_resp = client.post(f"/jobs/{job_id}/run")
    assert run_resp.status_code == 200

    artifacts_resp = client.get(f"/jobs/{job_id}/artifacts")
    body = artifacts_resp.json()

    assert artifacts_resp.status_code == 200
    assert body["job_id"] == job_id
    assert body["artifact_count"] == 2
    assert body["artifacts"][0]["relative_path"] == "gblup/gebv_predictions.csv"
    assert body["artifacts"][1]["relative_path"] == "gblup/model_summary.txt"


def test_job_artifacts_returns_409_for_unfinished_job(monkeypatch, tmp_path) -> None:
    _patch_llm(monkeypatch)

    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text("animal_id,daily_gain,sex\nA1,1.2,M\n", encoding="utf-8")
    genotype_file = tmp_path / "geno.vcf"
    genotype_file.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")

    client = TestClient(create_app())
    submit = client.post(
        "/jobs",
        json={
            "user_message": "Run genomic selection for daily_gain",
            "trait_name": "daily_gain",
            "phenotype_path": str(phenotype_file),
            "genotype_path": str(genotype_file),
        },
    )
    job_id = submit.json()["job_id"]

    artifacts_resp = client.get(f"/jobs/{job_id}/artifacts")
    assert artifacts_resp.status_code == 409
