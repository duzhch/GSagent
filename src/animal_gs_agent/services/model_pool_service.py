"""Model pool planning for strategy-search stage."""

import os

from animal_gs_agent.schemas.dataset_profile import DatasetProfile
from animal_gs_agent.schemas.model_pool import ModelCandidatePlan, ModelPoolPlan
from animal_gs_agent.schemas.task_understanding import TaskUnderstandingResult


def _bayesb_min_trait_records() -> int:
    raw = os.getenv("ANIMAL_GS_AGENT_MODEL_BAYESB_MIN_TRAIT_RECORDS", "30")
    try:
        value = int(raw)
    except ValueError:
        return 30
    return max(value, 1)


def _has_flag(profile: DatasetProfile, flag: str) -> bool:
    return flag in profile.validation_flags


def _trait_value_count(profile: DatasetProfile) -> int:
    if profile.phenotype_diagnostics is None:
        return 0
    return profile.phenotype_diagnostics.trait_value_count


def _evaluate_gblup(profile: DatasetProfile) -> ModelCandidatePlan:
    reasons: list[str] = []
    if not profile.trait_column_present or _has_flag(profile, "trait_column_missing"):
        reasons.append("trait_column_missing")
    return ModelCandidatePlan(model_id="GBLUP", available=not reasons, disabled_reasons=reasons)


def _evaluate_bayesb(profile: DatasetProfile) -> ModelCandidatePlan:
    reasons: list[str] = []
    if not profile.trait_column_present or _has_flag(profile, "trait_column_missing"):
        reasons.append("trait_column_missing")
    if _trait_value_count(profile) < _bayesb_min_trait_records():
        reasons.append("insufficient_trait_records_for_bayesb")
    return ModelCandidatePlan(model_id="BayesB", available=not reasons, disabled_reasons=reasons)


def _evaluate_xgboost(profile: DatasetProfile) -> ModelCandidatePlan:
    reasons: list[str] = []
    if _has_flag(profile, "qc_risk_high"):
        reasons.append("qc_risk_high")
    if not profile.trait_column_present or _has_flag(profile, "trait_column_missing"):
        reasons.append("trait_column_missing")
    return ModelCandidatePlan(model_id="XGBoost", available=not reasons, disabled_reasons=reasons)


def build_model_pool_plan(
    task_understanding: TaskUnderstandingResult,
    dataset_profile: DatasetProfile,
) -> ModelPoolPlan:
    if task_understanding.request_scope != "supported_gs":
        blocked = [
            ModelCandidatePlan(
                model_id=model_id,
                available=False,
                disabled_reasons=["unsupported_request_scope"],
            )
            for model_id in ("GBLUP", "BayesB", "XGBoost")
        ]
        return ModelPoolPlan(candidates=blocked, available_models=[])

    candidates = [
        _evaluate_gblup(dataset_profile),
        _evaluate_bayesb(dataset_profile),
        _evaluate_xgboost(dataset_profile),
    ]
    available_models = [item.model_id for item in candidates if item.available]
    return ModelPoolPlan(candidates=candidates, available_models=available_models)
