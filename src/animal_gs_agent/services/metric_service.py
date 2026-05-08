"""Metric calculation services."""

from __future__ import annotations

from math import sqrt

from animal_gs_agent.schemas.metric import AggregatedMetricResult, TrialMetricResult


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
