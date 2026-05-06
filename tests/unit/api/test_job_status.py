from fastapi.testclient import TestClient

from animal_gs_agent.api.app import create_app


def test_get_job_returns_submitted_job_status() -> None:
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
    }
