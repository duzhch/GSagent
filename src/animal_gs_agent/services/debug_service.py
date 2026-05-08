"""Debug-agent style failure classification and retry policy recommendations."""

from __future__ import annotations

from animal_gs_agent.schemas.debug import DebugDiagnosis


def classify_failure_category(*, error_code: str, error_message: str) -> str:
    merged = f"{error_code} {error_message}".lower()
    if any(token in merged for token in ["missing", "invalid", "trait_column", "dataset", "format"]):
        return "data"
    if any(token in merged for token in ["oom", "out of memory", "memory", "disk", "quota", "cpu", "gpu"]):
        return "resource"
    if any(token in merged for token in ["syntax", "exception", "traceback", "runtime_error", "workflow_runtime"]):
        return "code"
    return "environment"


def should_escalate_after_attempt(*, attempt: int, max_attempts: int, retryable: bool) -> bool:
    if not retryable:
        return True
    return attempt >= max_attempts


def _action_for_category(category: str) -> str:
    if category == "data":
        return "fix dataset quality/format issues before rerun"
    if category == "code":
        return "inspect workflow script and patch runtime failure point"
    if category == "resource":
        return "increase resource request or reduce workload per trial"
    return "repair runtime environment dependencies before rerun"


def _retryable_for_category(category: str) -> bool:
    if category == "data":
        return False
    return True


def build_debug_diagnosis(
    *,
    error_code: str,
    error_message: str,
    attempt: int,
    max_attempts: int,
) -> DebugDiagnosis:
    category = classify_failure_category(error_code=error_code, error_message=error_message)
    retryable = _retryable_for_category(category)
    escalate_immediately = should_escalate_after_attempt(
        attempt=attempt,
        max_attempts=max_attempts,
        retryable=retryable,
    )
    decision = "escalate" if escalate_immediately else "retry"
    return DebugDiagnosis(
        category=category,  # type: ignore[arg-type]
        retryable=retryable,
        suggested_retry_decision=decision,  # type: ignore[arg-type]
        suggested_action=_action_for_category(category),
        attempt=max(1, attempt),
        max_attempts=max(1, max_attempts),
        escalate_immediately=escalate_immediately,
    )
