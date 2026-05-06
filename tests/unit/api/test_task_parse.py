from fastapi.testclient import TestClient

from animal_gs_agent.api.app import create_app


def test_parse_task_route_returns_503_when_llm_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("ANIMAL_GS_AGENT_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("ANIMAL_GS_AGENT_LLM_API_KEY", raising=False)
    monkeypatch.delenv("ANIMAL_GS_AGENT_LLM_MODEL", raising=False)

    client = TestClient(create_app())

    response = client.post(
        "/agent/parse-task",
        json={
            "user_message": "Run genomic selection for trait daily_gain with sex and batch effects."
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "LLM provider is not configured"


def test_parse_task_route_returns_structured_result(monkeypatch) -> None:
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
        "/agent/parse-task",
        json={
            "user_message": "Run genomic selection for trait daily_gain with sex and batch effects."
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["request_scope"] == "supported_gs"
    assert body["trait_name"] == "daily_gain"
    assert "sex" in body["candidate_fixed_effects"]
    assert "batch" in body["candidate_fixed_effects"]
