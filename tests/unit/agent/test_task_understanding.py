from animal_gs_agent.agent.task_understanding import understand_task


class StubLLMClient:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def request_json(self, system_prompt: str, user_prompt: str) -> dict:
        assert "genomic selection" in user_prompt.lower()
        return self.payload


class FailingLLMClient:
    def request_json(self, system_prompt: str, user_prompt: str) -> dict:
        raise RuntimeError("provider unavailable")


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


def test_understand_task_falls_back_to_rules_when_provider_fails() -> None:
    result = understand_task(
        "Run genomic selection for trait daily_gain with sex and batch effects.",
        llm_client=FailingLLMClient(),
    )

    assert result.request_scope == "supported_gs"
    assert result.trait_name == "daily_gain"
    assert "sex" in result.candidate_fixed_effects
    assert "batch" in result.candidate_fixed_effects
