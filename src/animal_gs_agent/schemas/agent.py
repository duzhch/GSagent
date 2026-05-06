"""Schemas for agent-facing APIs."""

from pydantic import BaseModel


class ParseTaskRequest(BaseModel):
    user_message: str

