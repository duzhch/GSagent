from animal_gs_agent.agent.graph import classify_request
from animal_gs_agent.agent.state import IntakeState


def test_classify_request_marks_gs_request_as_supported() -> None:
    state = IntakeState(user_message="Please run genomic selection for trait milk_yield")

    updated = classify_request(state)

    assert updated["request_scope"] == "supported_gs"
