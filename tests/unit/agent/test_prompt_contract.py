from animal_gs_agent.agent.prompts import TASK_UNDERSTANDING_SYSTEM_PROMPT


def test_task_understanding_prompt_declares_required_json_keys() -> None:
    required = [
        "request_scope",
        "trait_name",
        "user_goal",
        "candidate_fixed_effects",
        "population_description",
        "missing_inputs",
        "confidence",
        "clarification_needed",
    ]
    for key in required:
        assert key in TASK_UNDERSTANDING_SYSTEM_PROMPT


def test_task_understanding_prompt_declares_runtime_tool_policy() -> None:
    assert "recommended_runtime_tools" in TASK_UNDERSTANDING_SYSTEM_PROMPT
    assert "recommended_execution_policy" in TASK_UNDERSTANDING_SYSTEM_PROMPT
    for tool in ("plink2", "nextflow", "Rscript", "sbatch"):
        assert tool in TASK_UNDERSTANDING_SYSTEM_PROMPT
