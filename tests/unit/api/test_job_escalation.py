from fastapi.testclient import TestClient

from animal_gs_agent.api.app import create_app
from animal_gs_agent.services.job_service import mark_job_escalated


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


def test_retry_escalated_job_requires_reason_and_requeues(monkeypatch, tmp_path) -> None:
    _patch_llm(monkeypatch)
    monkeypatch.setenv("ANIMAL_GS_AGENT_ASYNC_RUN_ENABLED", "1")
    monkeypatch.setenv("ANIMAL_GS_AGENT_RUN_QUEUE_SQLITE_PATH", str(tmp_path / "queue.db"))

    captured = {"job_id": None}

    def fake_enqueue(job_id: str) -> str:
        captured["job_id"] = job_id
        return "enqueued"

    monkeypatch.setattr("animal_gs_agent.api.routes.jobs.enqueue_run_job", fake_enqueue)

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
    mark_job_escalated(job_id, "max_attempts_exceeded")

    response = client.post(
        f"/jobs/{job_id}/escalation/retry",
        json={"approver": "qa_reviewer", "reason": "data fixed and approved for retry"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "queued"
    assert body["escalation_required"] is False
    assert captured["job_id"] == job_id


def test_abort_escalated_job_records_manual_abort(monkeypatch, tmp_path) -> None:
    _patch_llm(monkeypatch)

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
    mark_job_escalated(job_id, "max_attempts_exceeded")

    response = client.post(
        f"/jobs/{job_id}/escalation/abort",
        json={"approver": "qa_reviewer", "reason": "stop this run"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "failed"
    assert body["escalation_required"] is False
    assert body["execution_error"] == "manual_abort_after_escalation"
    assert body["decision_trace"][-1]["action"] == "approve_escalation_abort"
    assert body["fallback_plan"]["strategy"] == "manual_review_with_fixed_pipeline_fallback"
    assert body["fallback_plan"]["reason"] == "stop this run"
    assert body["fallback_plan"]["created_by"] == "qa_reviewer"


def test_retry_non_escalated_job_returns_409(monkeypatch, tmp_path) -> None:
    _patch_llm(monkeypatch)

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

    response = client.post(
        f"/jobs/{job_id}/escalation/retry",
        json={"approver": "qa_reviewer", "reason": "retry"},
    )
    assert response.status_code == 409
