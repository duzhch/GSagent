from animal_gs_agent.schemas.task_understanding import TaskUnderstandingResult


def test_task_understanding_schema_accepts_expected_fields() -> None:
    result = TaskUnderstandingResult(
        request_scope="supported_gs",
        trait_name="daily_gain",
        user_goal="rank candidates for genomic selection",
        candidate_fixed_effects=["sex", "batch"],
        population_description="commercial pig population",
        missing_inputs=["phenotype_file"],
        confidence=0.81,
        clarification_needed=False,
    )

    assert result.request_scope == "supported_gs"
    assert result.candidate_fixed_effects == ["sex", "batch"]
    assert result.confidence == 0.81
