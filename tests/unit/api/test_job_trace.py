from fastapi.testclient import TestClient

from animal_gs_agent.api.app import create_app


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


def test_get_job_trace_returns_decision_nodes(monkeypatch) -> None:
    _patch_llm(monkeypatch)
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

    trace_response = client.get(f"/jobs/{job_id}/trace")
    body = trace_response.json()

    assert trace_response.status_code == 200
    assert body["job_id"] == job_id
    assert len(body["decision_trace"]) >= 1
    assert body["decision_trace"][0]["feature_id"] == "F-P0-01-02"
    assert body["decision_trace"][0]["action"] == "accept_job"


def test_get_job_trace_returns_404_for_missing_job() -> None:
    client = TestClient(create_app())
    trace_response = client.get("/jobs/missing123/trace")
    assert trace_response.status_code == 404
