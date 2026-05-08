"""Scenario validation protocol planning."""

from animal_gs_agent.schemas.dataset_profile import DatasetProfile
from animal_gs_agent.schemas.task_understanding import TaskUnderstandingResult
from animal_gs_agent.schemas.validation_protocol import (
    ScenarioValidationProtocol,
    ValidationProtocolPlan,
    ValidationSplitRecord,
)


def build_validation_protocol_plan(
    task_understanding: TaskUnderstandingResult,
    dataset_profile: DatasetProfile,
) -> ValidationProtocolPlan:
    population_label = task_understanding.population_description or "unspecified population"

    within_pop = ScenarioValidationProtocol(
        scenario_id="within_pop",
        split_records=[
            ValidationSplitRecord(
                split_id="within_pop_primary",
                train_population=population_label,
                validation_population=population_label,
                notes="within-pop k-fold validation",
            )
        ],
        metrics=["within_pop_pearson", "within_pop_rmse"],
    )
    cross_pop = ScenarioValidationProtocol(
        scenario_id="cross_pop",
        split_records=[
            ValidationSplitRecord(
                split_id="cross_pop_primary",
                train_population=population_label,
                validation_population="held-out population",
                notes="cross-pop holdout validation",
            )
        ],
        metrics=["cross_pop_pearson", "cross_pop_rmse"],
    )
    return ValidationProtocolPlan(protocols=[within_pop, cross_pop])
