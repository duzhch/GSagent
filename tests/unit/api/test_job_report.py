from fastapi.testclient import TestClient

from animal_gs_agent.api.app import create_app
from animal_gs_agent.schemas.jobs import RankedCandidate, WorkflowSummary
from animal_gs_agent.services.workflow_service import WorkflowExecutionResult


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


def test_job_report_returns_agent_explanation_after_completion(monkeypatch, tmp_path) -> None:
    _patch_llm(monkeypatch)

    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text("animal_id,daily_gain,sex\nA1,1.2,M\n", encoding="utf-8")
    genotype_file = tmp_path / "geno.vcf"
    genotype_file.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")

    def fake_execute_workflow(job):
        return WorkflowExecutionResult(
            backend="native_nextflow",
            command=["nextflow", "run", "main.nf"],
            result_dir=f"/tmp/{job.job_id}",
        )

    def fake_parse_outputs(result_dir, trait_name, top_n=10):
        return WorkflowSummary(
            trait_name=trait_name,
            total_candidates=100,
            top_candidates=[
                RankedCandidate(individual_id="A1001", gebv=1.2345, rank=1),
                RankedCandidate(individual_id="A1099", gebv=1.1023, rank=2),
            ],
            model_metrics={"h²": "0.42", "预测准确度 r": "0.71"},
            source_files=["gblup/gebv_predictions.csv", "gblup/model_summary.txt"],
        )

    monkeypatch.setattr("animal_gs_agent.api.routes.jobs.execute_fixed_workflow", fake_execute_workflow)
    monkeypatch.setattr("animal_gs_agent.api.routes.jobs.parse_workflow_outputs", fake_parse_outputs)

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

    run_resp = client.post(f"/jobs/{job_id}/run")
    assert run_resp.status_code == 200
    assert run_resp.json()["status"] == "completed"

    report_resp = client.get(f"/jobs/{job_id}/report")
    body = report_resp.json()

    assert report_resp.status_code == 200
    assert body["job_id"] == job_id
    assert body["trait_name"] == "daily_gain"
    assert "Agent" in body["report_text"]
    assert "Workflow" in body["report_text"]
    assert len(body["top_candidates"]) == 2
    assert body["top_candidates"][0]["individual_id"] == "A1001"


def test_job_report_returns_409_for_unfinished_job(monkeypatch, tmp_path) -> None:
    _patch_llm(monkeypatch)

    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text("animal_id,daily_gain,sex\nA1,1.2,M\n", encoding="utf-8")
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

    report_resp = client.get(f"/jobs/{job_id}/report")
    assert report_resp.status_code == 409


def test_job_report_includes_population_risk_tags(monkeypatch, tmp_path) -> None:
    _patch_llm(monkeypatch)

    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text("animal_id,daily_gain,sex\nA1,1.2,M\n", encoding="utf-8")
    genotype_file = tmp_path / "geno.vcf"
    genotype_file.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")

    eigenvec = tmp_path / "plink.eigenvec"
    eigenvec.write_text(
        "\n".join(
            [
                "#FID IID PC1 PC2",
                "F1 A1 0.10 0.10",
                "F1 A2 0.20 0.20",
                "F1 A3 5.00 5.00",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ANIMAL_GS_AGENT_PLINK2_PCA_EIGENVEC_PATH", str(eigenvec))
    monkeypatch.setenv("ANIMAL_GS_AGENT_QC_PCA_ZSCORE_THRESHOLD", "1.0")

    def fake_execute_workflow(job):
        return WorkflowExecutionResult(
            backend="native_nextflow",
            command=["nextflow", "run", "main.nf"],
            result_dir=f"/tmp/{job.job_id}",
        )

    def fake_parse_outputs(result_dir, trait_name, top_n=10):
        return WorkflowSummary(
            trait_name=trait_name,
            total_candidates=10,
            top_candidates=[RankedCandidate(individual_id="A1001", gebv=1.2345, rank=1)],
            model_metrics={},
            source_files=["gblup/gebv_predictions.csv"],
        )

    monkeypatch.setattr("animal_gs_agent.api.routes.jobs.execute_fixed_workflow", fake_execute_workflow)
    monkeypatch.setattr("animal_gs_agent.api.routes.jobs.parse_workflow_outputs", fake_parse_outputs)

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

    run_resp = client.post(f"/jobs/{job_id}/run")
    assert run_resp.status_code == 200
    assert run_resp.json()["status"] == "completed"

    report_resp = client.get(f"/jobs/{job_id}/report")
    assert report_resp.status_code == 200
    assert "population_structure_outliers" in report_resp.json()["report_text"]


def test_job_report_includes_covariate_recommendation_when_batch_effect_significant(
    monkeypatch, tmp_path
) -> None:
    _patch_llm(monkeypatch)

    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text(
        "\n".join(
            [
                "animal_id,daily_gain,batch",
                "A1,1.0,B1",
                "A2,1.1,B1",
                "A3,6.0,B2",
                "A4,6.2,B2",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    genotype_file = tmp_path / "geno.vcf"
    genotype_file.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")

    monkeypatch.setenv("ANIMAL_GS_AGENT_PHENO_BATCH_COLUMN", "batch")
    monkeypatch.setenv("ANIMAL_GS_AGENT_PHENO_BATCH_EFFECT_MIN_ETA2", "0.20")

    def fake_execute_workflow(job):
        return WorkflowExecutionResult(
            backend="native_nextflow",
            command=["nextflow", "run", "main.nf"],
            result_dir=f"/tmp/{job.job_id}",
        )

    def fake_parse_outputs(result_dir, trait_name, top_n=10):
        return WorkflowSummary(
            trait_name=trait_name,
            total_candidates=10,
            top_candidates=[RankedCandidate(individual_id="A1001", gebv=1.2345, rank=1)],
            model_metrics={},
            source_files=["gblup/gebv_predictions.csv"],
        )

    monkeypatch.setattr("animal_gs_agent.api.routes.jobs.execute_fixed_workflow", fake_execute_workflow)
    monkeypatch.setattr("animal_gs_agent.api.routes.jobs.parse_workflow_outputs", fake_parse_outputs)

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
    run_resp = client.post(f"/jobs/{job_id}/run")
    assert run_resp.status_code == 200
    assert run_resp.json()["status"] == "completed"

    report_resp = client.get(f"/jobs/{job_id}/report")
    assert report_resp.status_code == 200
    assert "covariate=batch" in report_resp.json()["report_text"]


def test_job_report_includes_knowledge_citations(monkeypatch, tmp_path) -> None:
    _patch_llm(monkeypatch)

    phenotype_file = tmp_path / "pheno.csv"
    phenotype_file.write_text(
        "\n".join(
            [
                "animal_id,daily_gain,batch",
                "A1,1.0,B1",
                "A2,1.1,B1",
                "A3,6.0,B2",
                "A4,6.2,B2",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    genotype_file = tmp_path / "geno.vcf"
    genotype_file.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")

    sop_path = tmp_path / "sop.md"
    sop_path.write_text("SOP: For significant batch effect, add covariate=batch.", encoding="utf-8")
    literature_path = tmp_path / "literature.txt"
    literature_path.write_text("Paper: covariate=batch can reduce bias under batch drift.", encoding="utf-8")

    monkeypatch.setenv("ANIMAL_GS_AGENT_PHENO_BATCH_COLUMN", "batch")
    monkeypatch.setenv("ANIMAL_GS_AGENT_PHENO_BATCH_EFFECT_MIN_ETA2", "0.20")
    monkeypatch.setenv("ANIMAL_GS_AGENT_KNOWLEDGE_SOP_PATHS", str(sop_path))
    monkeypatch.setenv("ANIMAL_GS_AGENT_KNOWLEDGE_LITERATURE_PATHS", str(literature_path))

    def fake_execute_workflow(job):
        return WorkflowExecutionResult(
            backend="native_nextflow",
            command=["nextflow", "run", "main.nf"],
            result_dir=f"/tmp/{job.job_id}",
        )

    def fake_parse_outputs(result_dir, trait_name, top_n=10):
        return WorkflowSummary(
            trait_name=trait_name,
            total_candidates=10,
            top_candidates=[RankedCandidate(individual_id="A1001", gebv=1.2345, rank=1)],
            model_metrics={},
            source_files=["gblup/gebv_predictions.csv"],
        )

    monkeypatch.setattr("animal_gs_agent.api.routes.jobs.execute_fixed_workflow", fake_execute_workflow)
    monkeypatch.setattr("animal_gs_agent.api.routes.jobs.parse_workflow_outputs", fake_parse_outputs)

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
    run_resp = client.post(f"/jobs/{job_id}/run")
    assert run_resp.status_code == 200
    assert run_resp.json()["status"] == "completed"

    report_resp = client.get(f"/jobs/{job_id}/report")
    assert report_resp.status_code == 200
    citations = report_resp.json()["knowledge_citations"]
    assert len(citations) >= 1
    assert "covariate=batch" in citations[0]["recommendation"]
    assert len(citations[0]["evidence"]) >= 1
