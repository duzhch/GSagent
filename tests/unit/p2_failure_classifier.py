from animal_gs_agent.services.debug_service import (
    build_debug_diagnosis,
    classify_failure_category,
    should_escalate_after_attempt,
)


def test_failure_classifier_maps_error_to_expected_categories() -> None:
    assert classify_failure_category(error_code="trait_column_missing", error_message="missing trait") == "data"
    assert classify_failure_category(error_code="workflow_runtime_error", error_message="syntax error in script") == "code"
    assert classify_failure_category(error_code="slurm_oom", error_message="out of memory on node") == "resource"
    assert classify_failure_category(error_code="environment_not_ready", error_message="module load failed") == "environment"


def test_debug_retry_policy_recommends_action_and_retry_budget() -> None:
    diagnosis = build_debug_diagnosis(
        error_code="workflow_runtime_error",
        error_message="nextflow process syntax error",
        attempt=1,
        max_attempts=3,
    )

    assert diagnosis.category == "code"
    assert diagnosis.retryable is True
    assert diagnosis.suggested_action != ""
    assert diagnosis.suggested_retry_decision == "retry"
    assert diagnosis.escalate_immediately is False


def test_escalation_stop_triggers_when_attempt_budget_exhausted() -> None:
    assert should_escalate_after_attempt(attempt=3, max_attempts=3, retryable=True) is True
    assert should_escalate_after_attempt(attempt=1, max_attempts=3, retryable=False) is True
    assert should_escalate_after_attempt(attempt=1, max_attempts=3, retryable=True) is False
