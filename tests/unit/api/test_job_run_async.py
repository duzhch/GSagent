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


def test_run_job_enqueues_when_async_mode_enabled(monkeypatch, tmp_path) -> None:
    _patch_llm(monkeypatch)
    monkeypatch.setenv("ANIMAL_GS_AGENT_ASYNC_RUN_ENABLED", "1")

    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text("animal_id,daily_gain,sex\nA1,1.2,M\n", encoding="utf-8")
    genotype_file = tmp_path / "geno.vcf"
    genotype_file.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")

    captured = {"job_id": None}

    def fake_enqueue(job_id: str) -> str:
        captured["job_id"] = job_id
        return "enqueued"

    monkeypatch.setattr("animal_gs_agent.api.routes.jobs.enqueue_run_job", fake_enqueue)
    monkeypatch.setattr(
        "animal_gs_agent.api.routes.jobs.execute_fixed_workflow",
        lambda job: (_ for _ in ()).throw(AssertionError("workflow executor should not run in async mode")),
    )

    client = TestClient(create_app())
    submit_response = client.post(
        "/jobs",
        json={
            "user_message": "Run genomic selection for daily_gain",
            "trait_name": "daily_gain",
            "phenotype_path": str(phenotype_file),
            "genotype_path": str(genotype_file),
        },
    )
    job_id = submit_response.json()["job_id"]

    run_response = client.post(f"/jobs/{job_id}/run")
    body = run_response.json()

    assert run_response.status_code == 200
    assert captured["job_id"] == job_id
    assert body["status"] == "queued"
    assert body["events"][-1]["message"] == "queued for async worker execution"
