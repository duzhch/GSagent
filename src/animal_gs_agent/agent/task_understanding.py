"""Task understanding pipeline with model-backed and heuristic parsing."""

from __future__ import annotations

import re

from animal_gs_agent.agent.prompts import TASK_UNDERSTANDING_SYSTEM_PROMPT
from animal_gs_agent.schemas.task_understanding import TaskUnderstandingResult


class TaskUnderstandingError(Exception):
    """Base class for task understanding failures."""


class TaskUnderstandingProviderError(TaskUnderstandingError):
    """Raised when the upstream model provider call fails."""


class TaskUnderstandingValidationError(TaskUnderstandingError):
    """Raised when the provider response cannot be validated."""


def _has_meaningful_task_fields(payload: dict) -> bool:
    return any(
        [
            payload.get("trait_name"),
            payload.get("user_goal"),
            payload.get("candidate_fixed_effects"),
            payload.get("population_description"),
        ]
    )


def _normalize_payload(payload: dict) -> dict:
    normalized = dict(payload)

    if "trait_name" not in normalized and "trait" in normalized:
        normalized["trait_name"] = normalized["trait"]

    if "user_goal" not in normalized and "goal" in normalized:
        normalized["user_goal"] = normalized["goal"]

    if "candidate_fixed_effects" not in normalized and "fixed_effects" in normalized:
        normalized["candidate_fixed_effects"] = normalized["fixed_effects"]

    if "population_description" not in normalized and "population" in normalized:
        normalized["population_description"] = normalized["population"]

    normalized.setdefault("request_scope", "supported_gs")
    normalized.setdefault("missing_inputs", [])
    normalized.setdefault("confidence", 0.8)
    normalized.setdefault("clarification_needed", False)

    return normalized


def understand_task(user_message: str, llm_client) -> TaskUnderstandingResult:
    system_prompt = TASK_UNDERSTANDING_SYSTEM_PROMPT
    try:
        payload = llm_client.request_json(system_prompt=system_prompt, user_prompt=user_message)
    except Exception as exc:
        raise TaskUnderstandingProviderError(f"task understanding provider failed: {exc}") from exc

    try:
        normalized = _normalize_payload(payload)
        if not _has_meaningful_task_fields(normalized):
            raise TaskUnderstandingValidationError("invalid task understanding payload")
        return TaskUnderstandingResult.model_validate(normalized)
    except Exception as exc:
        if isinstance(exc, TaskUnderstandingValidationError):
            raise
        raise TaskUnderstandingValidationError("invalid task understanding payload") from exc


_FIXED_EFFECT_CANDIDATES = (
    "sex",
    "batch",
    "farm",
    "herd",
    "parity",
    "pen",
    "line",
    "year",
    "season",
)


def understand_task_heuristic(user_message: str, trait_name: str | None = None) -> TaskUnderstandingResult:
    """Build a conservative local parse when LLM is unavailable.

    This keeps the harness runnable in offline delivery mode.
    """

    lowered = user_message.lower()
    extracted_effects: list[str] = []
    for token in _FIXED_EFFECT_CANDIDATES:
        if re.search(rf"\b{re.escape(token)}\b", lowered):
            extracted_effects.append(token)

    if trait_name is None:
        match = re.search(r"\bfor\s+([a-zA-Z0-9_]+)", user_message)
        if match:
            trait_name = match.group(1)

    return TaskUnderstandingResult(
        request_scope="supported_gs",
        trait_name=trait_name,
        user_goal="rank candidates for genomic selection",
        candidate_fixed_effects=extracted_effects,
        population_description="unspecified population",
        missing_inputs=[],
        confidence=0.6,
        clarification_needed=False,
    )
