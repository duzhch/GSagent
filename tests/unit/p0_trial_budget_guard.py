from animal_gs_agent.services.trial_orchestrator_service import build_trial_plan


def test_trial_plan_never_exceeds_max_trials() -> None:
    result = build_trial_plan(
        max_trials=3,
        candidate_models=["GBLUP", "BayesB", "XGBoost"],
        random_seed=7,
        early_stop_patience=999,
    )

    assert result.budget_consumed == 3
    assert len(result.trials) == 3
    assert result.stop_reason == "budget_exhausted"


def test_trial_plan_can_stop_early_with_reason() -> None:
    result = build_trial_plan(
        max_trials=10,
        candidate_models=["GBLUP", "BayesB"],
        random_seed=1,
        early_stop_patience=1,
        min_improvement=2.0,
    )

    assert len(result.trials) < 10
    assert result.stop_reason == "early_stop_no_improvement"


def test_trial_plan_is_reproducible_with_same_seed() -> None:
    first = build_trial_plan(
        max_trials=5,
        candidate_models=["GBLUP", "BayesB", "XGBoost"],
        random_seed=42,
        early_stop_patience=999,
    )
    second = build_trial_plan(
        max_trials=5,
        candidate_models=["GBLUP", "BayesB", "XGBoost"],
        random_seed=42,
        early_stop_patience=999,
    )

    assert first.selected_model == second.selected_model
    assert first.stop_reason == second.stop_reason
    assert [(t.trial_index, t.model_id, t.score) for t in first.trials] == [
        (t.trial_index, t.model_id, t.score) for t in second.trials
    ]
