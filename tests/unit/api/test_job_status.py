from fastapi.testclient import TestClient

from animal_gs_agent.api.app import create_app


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

    assert response.status_code == 200
    assert response.json() == {
        "job_id": job_id,
        "status": "pending",
        "trait_name": "daily_gain",
        "task_understanding": {
            "request_scope": "supported_gs",
            "trait_name": "daily_gain",
            "user_goal": "rank candidates for genomic selection",
            "candidate_fixed_effects": ["sex", "batch"],
            "population_description": "commercial pig population",
            "missing_inputs": [],
            "confidence": 0.91,
            "clarification_needed": False,
        },
    }
