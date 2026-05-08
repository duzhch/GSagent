"""Trial orchestration service under explicit budget constraints."""

from __future__ import annotations

import random

from animal_gs_agent.schemas.trial_strategy import TrialPlanResult, TrialRecord


def build_trial_plan(
    *,
    max_trials: int,
    candidate_models: list[str],
    random_seed: int | None = None,
    early_stop_patience: int = 3,
    min_improvement: float = 0.0,
) -> TrialPlanResult:
    if max_trials <= 0:
        raise ValueError("max_trials must be greater than 0")

    if not candidate_models:
        return TrialPlanResult(
            trials=[],
            selected_model=None,
            budget_consumed=0,
            stop_reason="no_candidate_models",
            random_seed=random_seed,
        )

    patience = max(1, early_stop_patience)
    rng = random.Random(random_seed)

    trials: list[TrialRecord] = []
    selected_model: str | None = None
    best_score: float | None = None
    no_improvement_count = 0
    stop_reason = "budget_exhausted"

    for i in range(max_trials):
        model_id = candidate_models[i % len(candidate_models)]
        score = rng.random()

        if best_score is None:
            is_new_best = True
        else:
            is_new_best = (score - best_score) > min_improvement

        if is_new_best:
            best_score = score
            selected_model = model_id
            no_improvement_count = 0
        else:
            no_improvement_count += 1

        trials.append(
            TrialRecord(
                trial_index=i + 1,
                model_id=model_id,
                score=score,
                is_new_best=is_new_best,
            )
        )

        if no_improvement_count >= patience and (i + 1) < max_trials:
            stop_reason = "early_stop_no_improvement"
            break

    return TrialPlanResult(
        trials=trials,
        selected_model=selected_model,
        budget_consumed=len(trials),
        stop_reason=stop_reason,
        random_seed=random_seed,
    )
