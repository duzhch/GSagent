"""Metric calculation services."""

from __future__ import annotations

from math import sqrt

from animal_gs_agent.schemas.metric import (
    AggregatedMetricResult,
    DecisionQualityResult,
    SearchEfficiencyResult,
    TrialMetricResult,
)


def _pearson(y_true: list[float], y_pred: list[float]) -> float:
    n = len(y_true)
    if n == 0 or n != len(y_pred):
        raise ValueError("y_true and y_pred must have same non-zero length")
    if n == 1:
        return 0.0

    mean_true = sum(y_true) / n
    mean_pred = sum(y_pred) / n
    centered_true = [v - mean_true for v in y_true]
    centered_pred = [v - mean_pred for v in y_pred]

    numerator = sum(a * b for a, b in zip(centered_true, centered_pred))
    denom_true = sqrt(sum(a * a for a in centered_true))
    denom_pred = sqrt(sum(b * b for b in centered_pred))
    if denom_true == 0.0 or denom_pred == 0.0:
        return 0.0
    value = numerator / (denom_true * denom_pred)
    return max(-1.0, min(1.0, value))


def _rmse(y_true: list[float], y_pred: list[float]) -> float:
    n = len(y_true)
    if n == 0 or n != len(y_pred):
        raise ValueError("y_true and y_pred must have same non-zero length")
    mse = sum((a - b) ** 2 for a, b in zip(y_true, y_pred)) / n
    return sqrt(mse)


def compute_trial_metrics(
    *,
    y_true: list[float],
    y_pred: list[float],
    population: str,
    trait: str,
    model_id: str,
) -> TrialMetricResult:
    return TrialMetricResult(
        population=population,
        trait=trait,
        model_id=model_id,
        pearson=_pearson(y_true, y_pred),
        rmse=_rmse(y_true, y_pred),
    )


def aggregate_trial_metrics(records: list[TrialMetricResult]) -> list[AggregatedMetricResult]:
    if not records:
        return []

    grouped: dict[tuple[str, str, str], list[TrialMetricResult]] = {}
    for item in records:
        key = (item.population, item.trait, item.model_id)
        grouped.setdefault(key, []).append(item)

    result: list[AggregatedMetricResult] = []
    for (population, trait, model_id), items in grouped.items():
        count = len(items)
        result.append(
            AggregatedMetricResult(
                population=population,
                trait=trait,
                model_id=model_id,
                trial_count=count,
                mean_pearson=sum(i.pearson for i in items) / count,
                mean_rmse=sum(i.rmse for i in items) / count,
            )
        )
    return result


def compute_decision_quality(
    *,
    candidate_scores: dict[str, float],
    selected_model_id: str,
    oracle_best_score: float | None,
) -> DecisionQualityResult:
    selected_score = candidate_scores.get(selected_model_id)
    if selected_score is None:
        raise ValueError(f"selected_model_id not found in candidate_scores: {selected_model_id}")

    best_candidate_score = max(candidate_scores.values()) if candidate_scores else selected_score
    top1_hit = selected_score >= best_candidate_score

    if oracle_best_score is None:
        return DecisionQualityResult(
            selected_model_id=selected_model_id,
            top1_hit=top1_hit,
            regret=None,
            not_computable_reason="oracle_best_missing",
        )

    regret = max(0.0, oracle_best_score - selected_score)
    return DecisionQualityResult(
        selected_model_id=selected_model_id,
        top1_hit=top1_hit,
        regret=regret,
        not_computable_reason=None,
    )


def compute_search_efficiency(
    *,
    trial_scores: list[float | None],
    invalid_reasons: list[str | None],
) -> SearchEfficiencyResult:
    if len(trial_scores) != len(invalid_reasons):
        raise ValueError("trial_scores and invalid_reasons must have the same length")

    total = len(trial_scores)
    valid_scores = [s for s in trial_scores if s is not None]
    valid_trials = len(valid_scores)
    invalid_trials = total - valid_trials
    invalid_rate = (invalid_trials / total) if total > 0 else 0.0

    reason_breakdown: dict[str, int] = {}
    for reason in invalid_reasons:
        if reason is None:
            continue
        reason_breakdown[reason] = reason_breakdown.get(reason, 0) + 1

    if valid_trials == 0:
        return SearchEfficiencyResult(
            total_trials=total,
            valid_trials=0,
            trials_to_95_best=None,
            invalid_trial_rate=invalid_rate,
            invalid_reason_breakdown=reason_breakdown,
            not_computable_reason="no_valid_trials",
        )

    best_score = max(valid_scores)
    threshold = best_score * 0.95
    trials_to_95: int | None = None
    for i, score in enumerate(trial_scores, start=1):
        if score is None:
            continue
        if score >= threshold:
            trials_to_95 = i
            break

    return SearchEfficiencyResult(
        total_trials=total,
        valid_trials=valid_trials,
        trials_to_95_best=trials_to_95,
        invalid_trial_rate=invalid_rate,
        invalid_reason_breakdown=reason_breakdown,
        not_computable_reason=None,
    )
