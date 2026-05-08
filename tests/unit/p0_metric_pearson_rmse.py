from animal_gs_agent.services.metric_service import aggregate_trial_metrics, compute_trial_metrics


def test_compute_trial_metrics_outputs_pearson_and_rmse() -> None:
    result = compute_trial_metrics(
        y_true=[1.0, 2.0, 3.0, 4.0],
        y_pred=[1.1, 1.9, 3.2, 3.8],
        population="pig5",
        trait="daily_gain",
        model_id="GBLUP",
    )

    assert result.population == "pig5"
    assert result.trait == "daily_gain"
    assert result.model_id == "GBLUP"
    assert -1.0 <= result.pearson <= 1.0
    assert result.rmse >= 0.0


def test_aggregate_trial_metrics_by_population_trait_model() -> None:
    records = [
        compute_trial_metrics(
            y_true=[1.0, 2.0, 3.0],
            y_pred=[1.1, 2.0, 3.1],
            population="pig5",
            trait="daily_gain",
            model_id="GBLUP",
        ),
        compute_trial_metrics(
            y_true=[1.0, 2.0, 3.0],
            y_pred=[1.2, 1.8, 3.0],
            population="pig5",
            trait="daily_gain",
            model_id="GBLUP",
        ),
        compute_trial_metrics(
            y_true=[1.0, 2.0, 3.0],
            y_pred=[0.9, 2.2, 2.8],
            population="pig6",
            trait="daily_gain",
            model_id="BayesB",
        ),
    ]

    grouped = aggregate_trial_metrics(records)
    by_key = {(g.population, g.trait, g.model_id): g for g in grouped}

    assert len(grouped) == 2
    pig5 = by_key[("pig5", "daily_gain", "GBLUP")]
    assert pig5.trial_count == 2
    assert -1.0 <= pig5.mean_pearson <= 1.0
    assert pig5.mean_rmse >= 0.0

    pig6 = by_key[("pig6", "daily_gain", "BayesB")]
    assert pig6.trial_count == 1
