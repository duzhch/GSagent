from fastapi.testclient import TestClient

from animal_gs_agent.api.app import create_app


def test_parse_task_route_returns_structured_result() -> None:
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

