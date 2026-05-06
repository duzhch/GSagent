from animal_gs_agent.agent.task_understanding import understand_task
from animal_gs_agent.agent.task_understanding import (
    TaskUnderstandingProviderError,
    TaskUnderstandingValidationError,
)


class StubLLMClient:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def request_json(self, system_prompt: str, user_prompt: str) -> dict:
        assert "genomic selection" in user_prompt.lower()
        return self.payload


class FailingLLMClient:
    def request_json(self, system_prompt: str, user_prompt: str) -> dict:
        raise RuntimeError("provider unavailable")


class InvalidPayloadLLMClient:
    def request_json(self, system_prompt: str, user_prompt: str) -> dict:
        return {"request_scope": "supported_gs"}


class NearMissPayloadLLMClient:
    def request_json(self, system_prompt: str, user_prompt: str) -> dict:
        return {
            "trait": "daily_gain",
            "goal": "rank candidates for genomic selection",
            "fixed_effects": ["sex", "batch"],
            "population": "commercial pig population",
        }


def test_understand_task_uses_llm_output_when_valid() -> None:
    client = StubLLMClient(
        {
            "request_scope": "supported_gs",
            "trait_name": "daily_gain",
            "user_goal": "rank candidates for genomic selection",
            "candidate_fixed_effects": ["sex", "batch"],
            "population_description": "commercial pig population",
            "missing_inputs": [],
            "confidence": 0.92,
            "clarification_needed": False,
        }
    )

    result = understand_task(
        "Run genomic selection for trait daily_gain in a commercial pig population.",
        llm_client=client,
    )

    assert result.trait_name == "daily_gain"
    assert result.candidate_fixed_effects == ["sex", "batch"]
    assert result.clarification_needed is False


def test_understand_task_raises_when_provider_fails() -> None:
    try:
        understand_task(
            "Run genomic selection for trait daily_gain with sex and batch effects.",
            llm_client=FailingLLMClient(),
        )
    except TaskUnderstandingProviderError as exc:
        assert "provider unavailable" in str(exc)
    else:
        raise AssertionError("expected TaskUnderstandingProviderError")


def test_understand_task_raises_when_payload_is_invalid() -> None:
    try:
        understand_task(
            "Run genomic selection for trait daily_gain.",
            llm_client=InvalidPayloadLLMClient(),
        )
    except TaskUnderstandingValidationError as exc:
        assert "invalid task understanding payload" in str(exc)
    else:
        raise AssertionError("expected TaskUnderstandingValidationError")


def test_understand_task_normalizes_near_miss_payload() -> None:
    result = understand_task(
        "Run genomic selection for trait daily_gain.",
        llm_client=NearMissPayloadLLMClient(),
    )

    assert result.request_scope == "supported_gs"
    assert result.trait_name == "daily_gain"
    assert result.user_goal == "rank candidates for genomic selection"
    assert result.candidate_fixed_effects == ["sex", "batch"]
