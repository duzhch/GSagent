from fastapi.testclient import TestClient

from animal_gs_agent.api.app import create_app


def test_submit_job_returns_pending_job(monkeypatch) -> None:
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

    response = client.post(
        "/jobs",
        json={
            "user_message": "Run genomic selection for daily_gain",
            "trait_name": "daily_gain",
            "phenotype_path": "data/demo/phenotypes.csv",
            "genotype_path": "data/demo/genotypes.pgen",
        },
    )

    body = response.json()

    assert response.status_code == 202
    assert body["status"] == "queued"
    assert body["trait_name"] == "daily_gain"
    assert body["task_understanding"]["request_scope"] == "supported_gs"
    assert body["task_understanding"]["candidate_fixed_effects"] == ["sex", "batch"]
    assert body["dataset_profile"]["phenotype_path"] == "data/demo/phenotypes.csv"
    assert body["dataset_profile"]["genotype_path"] == "data/demo/genotypes.pgen"
    assert body["dataset_profile"]["path_checks"]["phenotype_exists"] is False
    assert body["dataset_profile"]["path_checks"]["genotype_exists"] is False
    assert "job_id" in body


def test_submit_job_returns_503_when_llm_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("ANIMAL_GS_AGENT_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("ANIMAL_GS_AGENT_LLM_API_KEY", raising=False)
    monkeypatch.delenv("ANIMAL_GS_AGENT_LLM_MODEL", raising=False)

    client = TestClient(create_app())

    response = client.post(
        "/jobs",
        json={
            "user_message": "Run genomic selection for daily_gain with sex and batch fixed effects",
            "trait_name": "daily_gain",
            "phenotype_path": "data/demo/phenotypes.csv",
            "genotype_path": "data/demo/genotypes.vcf",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "LLM provider is not configured"
