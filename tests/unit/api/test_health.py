from fastapi.testclient import TestClient

from animal_gs_agent.api.app import create_app


def test_healthcheck_returns_service_identity() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "animal-gs-agent",
        "status": "ok",
    }
