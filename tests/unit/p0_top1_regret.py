from animal_gs_agent.services.metric_service import compute_decision_quality


def test_decision_quality_outputs_top1_and_regret() -> None:
    result = compute_decision_quality(
        candidate_scores={"GBLUP": 0.82, "BayesB": 0.85, "XGBoost": 0.80},
        selected_model_id="BayesB",
        oracle_best_score=0.85,
    )

    assert result.top1_hit is True
    assert result.regret == 0.0
    assert result.not_computable_reason is None


def test_decision_quality_returns_reason_when_oracle_missing() -> None:
    result = compute_decision_quality(
        candidate_scores={"GBLUP": 0.82, "BayesB": 0.85},
        selected_model_id="GBLUP",
        oracle_best_score=None,
    )

    assert result.top1_hit is False
    assert result.regret is None
    assert result.not_computable_reason == "oracle_best_missing"
