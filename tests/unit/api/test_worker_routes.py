from fastapi.testclient import TestClient

from animal_gs_agent.api.app import create_app


def test_worker_health_route_returns_operational_snapshot(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ANIMAL_GS_AGENT_RUN_QUEUE_SQLITE_PATH", str(tmp_path / "queue.db"))
    monkeypatch.setenv("ANIMAL_GS_AGENT_ASYNC_RUN_ENABLED", "1")

    client = TestClient(create_app())
    response = client.get("/worker/health")
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "ok"
    assert body["async_run_enabled"] is True
    assert body["pending_jobs"] == 0


def test_worker_process_once_route_processes_enqueued_job(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_API_KEY", "secret-key")
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("ANIMAL_GS_AGENT_ASYNC_RUN_ENABLED", "1")
    monkeypatch.setenv("ANIMAL_GS_AGENT_RUN_QUEUE_SQLITE_PATH", str(tmp_path / "queue.db"))
    monkeypatch.setenv("ANIMAL_GS_AGENT_JOB_STORE_SQLITE_PATH", str(tmp_path / "jobs.db"))

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
    monkeypatch.setattr(
        "animal_gs_agent.api.routes.worker.execute_fixed_workflow",
        lambda job: type(
            "ExecutionResult",
            (),
            {
                "backend": "native_nextflow",
                "command": ["nextflow", "run", "main.nf"],
                "result_dir": f"/tmp/{job.job_id}",
                "status": "completed",
                "submission_id": None,
            },
        )(),
    )
    monkeypatch.setattr(
        "animal_gs_agent.api.routes.worker.parse_workflow_outputs",
        lambda result_dir, trait_name, top_n=10: None,
    )

    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text("animal_id,daily_gain\nA1,1.2\n", encoding="utf-8")
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

    run_response = client.post(f"/jobs/{job_id}/run")
    assert run_response.status_code == 200
    assert run_response.json()["status"] == "queued"

    process_response = client.post("/worker/process-once")
    body = process_response.json()

    assert process_response.status_code == 200
    assert body["processed"] is True
    assert body["job_id"] == job_id
    assert body["job_status"] == "completed"
