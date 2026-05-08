from animal_gs_agent.services.metric_service import compute_search_efficiency


def test_search_efficiency_outputs_trials_to_95_and_invalid_rate() -> None:
    result = compute_search_efficiency(
        trial_scores=[0.20, 0.50, None, 0.90, 0.86],
        invalid_reasons=[None, None, "nan_prediction", None, None],
    )

    assert result.total_trials == 5
    assert result.valid_trials == 4
    assert result.trials_to_95_best == 4
    assert abs(result.invalid_trial_rate - 0.2) < 1e-9
    assert result.invalid_reason_breakdown["nan_prediction"] == 1
    assert result.not_computable_reason is None


def test_search_efficiency_returns_reason_when_all_trials_invalid() -> None:
    result = compute_search_efficiency(
        trial_scores=[None, None, None],
        invalid_reasons=["runtime_error", "runtime_error", "nan_prediction"],
    )

    assert result.total_trials == 3
    assert result.valid_trials == 0
    assert result.trials_to_95_best is None
    assert abs(result.invalid_trial_rate - 1.0) < 1e-9
    assert result.not_computable_reason == "no_valid_trials"
