from fastapi.testclient import TestClient

from animal_gs_agent.api.app import create_app


def test_submit_job_returns_pending_job() -> None:
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
    assert body["status"] == "pending"
    assert body["trait_name"] == "daily_gain"
    assert "job_id" in body
