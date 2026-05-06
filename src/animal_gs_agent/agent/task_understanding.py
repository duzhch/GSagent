"""Task understanding pipeline with model-backed parsing."""

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
    system_prompt = "You are a genomic selection request parser. Return strict JSON only."
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
