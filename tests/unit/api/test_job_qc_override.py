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


def _prepare_qc_high_env(monkeypatch, tmp_path) -> None:
    smiss = tmp_path / "plink.smiss"
    smiss.write_text(
        "\n".join(
            [
                "FID IID MISS_PHENO N_MISS N_GENO F_MISS",
                "A1 A1 0 20 100 0.200",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    vmiss = tmp_path / "plink.vmiss"
    vmiss.write_text(
        "\n".join(
            [
                "CHROM ID POS N_MISS N_GENO F_MISS",
                "1 rs1 100 10 1000 0.010",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ANIMAL_GS_AGENT_PLINK2_SMISS_PATH", str(smiss))
    monkeypatch.setenv("ANIMAL_GS_AGENT_PLINK2_VMISS_PATH", str(vmiss))
    monkeypatch.setenv("ANIMAL_GS_AGENT_QC_MISSINGNESS_HIGH_THRESHOLD", "0.10")


def _create_qc_blocked_job(monkeypatch, tmp_path, client: TestClient) -> str:
    _patch_llm(monkeypatch)
    _prepare_qc_high_env(monkeypatch, tmp_path)

    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text("animal_id,daily_gain\nA1,1.2\n", encoding="utf-8")
    genotype_file = tmp_path / "geno.bed"
    genotype_file.write_text("placeholder", encoding="utf-8")

    monkeypatch.setattr(
        "animal_gs_agent.api.routes.jobs.execute_fixed_workflow",
        lambda _job: (_ for _ in ()).throw(AssertionError("workflow should not run for blocked job")),
    )

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
    assert run_response.json()["execution_error"] == "qc_risk_high_blocked"
    return job_id


def test_qc_override_requeues_blocked_job(monkeypatch, tmp_path) -> None:
    client = TestClient(create_app())
    job_id = _create_qc_blocked_job(monkeypatch, tmp_path, client)

    response = client.post(
        f"/jobs/{job_id}/qc/override",
        json={"approver": "qa_reviewer", "reason": "allow run for controlled test"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "queued"
    assert body["qc_override_applied"] is True
    assert body["qc_override_by"] == "qa_reviewer"
    assert "execution_error" not in body or body["execution_error"] is None
    assert body["decision_trace"][-1]["action"] == "approve_qc_override"


def test_qc_override_returns_409_for_non_blocked_job(monkeypatch, tmp_path) -> None:
    _patch_llm(monkeypatch)
    client = TestClient(create_app())

    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text("animal_id,daily_gain\nA1,1.2\n", encoding="utf-8")
    genotype_file = tmp_path / "geno.vcf"
    genotype_file.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")

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
        f"/jobs/{job_id}/qc/override",
        json={"approver": "qa_reviewer", "reason": "retry"},
    )

    assert response.status_code == 409
