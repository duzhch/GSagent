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


def test_submit_job_rejects_when_scope_not_authorized(monkeypatch, tmp_path) -> None:
    _patch_llm(monkeypatch)

    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text("animal_id,daily_gain\nA1,1.2\n", encoding="utf-8")
    genotype_file = tmp_path / "geno.vcf"
    genotype_file.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")

    client = TestClient(create_app())
    response = client.post(
        "/jobs",
        json={
            "user_message": "Run genomic selection for daily_gain",
            "trait_name": "daily_gain",
            "phenotype_path": str(phenotype_file),
            "genotype_path": str(genotype_file),
            "project_scope": "project_a",
            "access_scopes": ["project_b"],
        },
    )
    assert response.status_code == 403


def test_submit_job_rejects_when_project_quota_exceeded(monkeypatch, tmp_path) -> None:
    _patch_llm(monkeypatch)
    monkeypatch.setenv("ANIMAL_GS_AGENT_PROJECT_QUOTA_MAX_ACTIVE", "1")

    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text("animal_id,daily_gain\nA1,1.2\n", encoding="utf-8")
    genotype_file = tmp_path / "geno.vcf"
    genotype_file.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")

    client = TestClient(create_app())
    first = client.post(
        "/jobs",
        json={
            "user_message": "Run genomic selection for daily_gain",
            "trait_name": "daily_gain",
            "phenotype_path": str(phenotype_file),
            "genotype_path": str(genotype_file),
            "project_scope": "project_a",
            "access_scopes": ["project_a"],
        },
    )
    assert first.status_code == 202

    second = client.post(
        "/jobs",
        json={
            "user_message": "Run genomic selection for daily_gain",
            "trait_name": "daily_gain",
            "phenotype_path": str(phenotype_file),
            "genotype_path": str(genotype_file),
            "project_scope": "project_a",
            "access_scopes": ["project_a"],
        },
    )
    assert second.status_code == 429


def test_governance_audit_endpoint_returns_observability_snapshot(monkeypatch, tmp_path) -> None:
    _patch_llm(monkeypatch)

    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text("animal_id,daily_gain\nA1,1.2\n", encoding="utf-8")
    genotype_file = tmp_path / "geno.vcf"
    genotype_file.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")

    def fake_execute_workflow(job):
        return WorkflowExecutionResult(
            backend="native_nextflow",
            command=["nextflow", "run", "main.nf"],
            result_dir=f"/tmp/{job.job_id}",
        )

    def fake_parse_outputs(result_dir, trait_name, top_n=10):
        return WorkflowSummary(
            trait_name=trait_name,
            total_candidates=1,
            top_candidates=[RankedCandidate(individual_id="A1", gebv=1.2, rank=1)],
            model_metrics={},
            source_files=["gblup/gebv_predictions.csv"],
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
            "project_scope": "project_a",
            "access_scopes": ["project_a"],
        },
    )
    job_id = submit.json()["job_id"]
    run_resp = client.post(f"/jobs/{job_id}/run")
    assert run_resp.status_code == 200

    audit_resp = client.get(f"/jobs/{job_id}/governance/audit")
    assert audit_resp.status_code == 200
    body = audit_resp.json()
    assert body["job_id"] == job_id
    assert body["event_count"] >= 1
    assert body["decision_count"] >= 1
    assert body["execution_status"] in {"completed", "failed", "running", "queued"}
