"""Typed state contracts for the agent graph."""

from typing import Literal

from typing_extensions import TypedDict


class IntakeState(TypedDict, total=False):
    user_message: str
    request_scope: Literal["supported_gs", "unsupported"]

