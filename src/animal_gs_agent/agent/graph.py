"""Minimal request-classification logic for the agent graph."""

from animal_gs_agent.agent.state import IntakeState


def classify_request(state: IntakeState) -> IntakeState:
    message = state["user_message"].lower()
    if "genomic selection" in message or "gs" in message:
        return {**state, "request_scope": "supported_gs"}
    return {**state, "request_scope": "unsupported"}
