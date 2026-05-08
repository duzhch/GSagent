from fastapi.testclient import TestClient

from animal_gs_agent.api.app import create_app
from animal_gs_agent.schemas.dataset_profile import (
    DatasetPathChecks,
    DatasetProfile,
    PhenotypeDiagnosticsSummary,
)


def test_submit_job_returns_pending_job(monkeypatch) -> None:
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
    assert body["status"] == "queued"
    assert body["trait_name"] == "daily_gain"
    assert body["task_understanding"]["request_scope"] == "supported_gs"
    assert body["task_understanding"]["candidate_fixed_effects"] == ["sex", "batch"]
    assert body["dataset_profile"]["phenotype_path"] == "data/demo/phenotypes.csv"
    assert body["dataset_profile"]["genotype_path"] == "data/demo/genotypes.pgen"
    assert body["dataset_profile"]["path_checks"]["phenotype_exists"] is False
    assert body["dataset_profile"]["path_checks"]["genotype_exists"] is False
    assert "job_id" in body


def test_submit_job_returns_503_when_llm_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("ANIMAL_GS_AGENT_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("ANIMAL_GS_AGENT_LLM_API_KEY", raising=False)
    monkeypatch.delenv("ANIMAL_GS_AGENT_LLM_MODEL", raising=False)

    client = TestClient(create_app())

    response = client.post(
        "/jobs",
        json={
            "user_message": "Run genomic selection for daily_gain with sex and batch fixed effects",
            "trait_name": "daily_gain",
            "phenotype_path": "data/demo/phenotypes.csv",
            "genotype_path": "data/demo/genotypes.vcf",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "LLM provider is not configured"


def test_submit_job_includes_model_pool_disable_reasons(monkeypatch) -> None:
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

    def fake_profile(payload) -> DatasetProfile:
        return DatasetProfile(
            phenotype_path=payload.phenotype_path,
            genotype_path=payload.genotype_path,
            path_checks=DatasetPathChecks(phenotype_exists=True, genotype_exists=True),
            phenotype_format="csv",
            genotype_format="vcf",
            phenotype_headers=["animal_id"],
            trait_column_present=False,
            validation_flags=["trait_column_missing", "qc_risk_high"],
            risk_tags=["phenotype_batch_effect_significant"],
            phenotype_diagnostics=PhenotypeDiagnosticsSummary(
                sample_count=20,
                trait_value_count=20,
                outlier_count=3,
                outlier_ratio=0.15,
                outlier_zscore_threshold=3.0,
                high_outlier_ratio_threshold=0.1,
                batch_column="batch",
                batch_level_count=2,
                batch_effect_eta2=0.4,
                batch_effect_significant=True,
                batch_effect_eta2_threshold=0.2,
                recommendations=["recommend covariate=batch"],
            ),
        )

    monkeypatch.setattr(
        "animal_gs_agent.llm.client.OpenAICompatibleLLMClient.request_json",
        fake_request_json,
    )
    monkeypatch.setattr("animal_gs_agent.api.routes.jobs.build_dataset_profile", fake_profile)

    client = TestClient(create_app())
    response = client.post(
        "/jobs",
        json={
            "user_message": "Run genomic selection for daily_gain",
            "trait_name": "daily_gain",
            "phenotype_path": "data/demo/phenotypes.csv",
            "genotype_path": "data/demo/genotypes.vcf",
        },
    )

    assert response.status_code == 202
    body = response.json()
    assert "model_pool_plan" in body
    by_model = {item["model_id"]: item for item in body["model_pool_plan"]["candidates"]}
    assert by_model["GBLUP"]["available"] is False
    assert "trait_column_missing" in by_model["GBLUP"]["disabled_reasons"]
    assert by_model["BayesB"]["available"] is False
    assert "insufficient_trait_records_for_bayesb" in by_model["BayesB"]["disabled_reasons"]
    assert by_model["XGBoost"]["available"] is False
    assert "qc_risk_high" in by_model["XGBoost"]["disabled_reasons"]


def test_submit_job_includes_trial_stop_reason(monkeypatch) -> None:
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_API_KEY", "secret-key")
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("ANIMAL_GS_AGENT_STRATEGY_MAX_TRIALS", "10")
    monkeypatch.setenv("ANIMAL_GS_AGENT_STRATEGY_EARLY_STOP_PATIENCE", "1")
    monkeypatch.setenv("ANIMAL_GS_AGENT_STRATEGY_MIN_IMPROVEMENT", "2.0")
    monkeypatch.setenv("ANIMAL_GS_AGENT_STRATEGY_RANDOM_SEED", "11")

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

    def fake_profile(payload) -> DatasetProfile:
        return DatasetProfile(
            phenotype_path=payload.phenotype_path,
            genotype_path=payload.genotype_path,
            path_checks=DatasetPathChecks(phenotype_exists=True, genotype_exists=True),
            phenotype_format="csv",
            genotype_format="vcf",
            phenotype_headers=["animal_id", "daily_gain"],
            trait_column_present=True,
            validation_flags=[],
            risk_tags=[],
            phenotype_diagnostics=PhenotypeDiagnosticsSummary(
                sample_count=300,
                trait_value_count=300,
                outlier_count=0,
                outlier_ratio=0.0,
                outlier_zscore_threshold=3.0,
                high_outlier_ratio_threshold=0.1,
                batch_column="batch",
                batch_level_count=2,
                batch_effect_eta2=0.05,
                batch_effect_significant=False,
                batch_effect_eta2_threshold=0.2,
                recommendations=[],
            ),
        )

    monkeypatch.setattr(
        "animal_gs_agent.llm.client.OpenAICompatibleLLMClient.request_json",
        fake_request_json,
    )
    monkeypatch.setattr("animal_gs_agent.api.routes.jobs.build_dataset_profile", fake_profile)

    client = TestClient(create_app())
    response = client.post(
        "/jobs",
        json={
            "user_message": "Run genomic selection for daily_gain",
            "trait_name": "daily_gain",
            "phenotype_path": "data/demo/phenotypes.csv",
            "genotype_path": "data/demo/genotypes.vcf",
        },
    )

    assert response.status_code == 202
    body = response.json()
    assert "trial_strategy_plan" in body
    assert body["trial_strategy_plan"]["stop_reason"] == "early_stop_no_improvement"
    assert body["trial_strategy_plan"]["budget_consumed"] < 10
