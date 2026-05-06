"""Application configuration."""

import os

from pydantic import BaseModel


class LLMSettings(BaseModel):
    provider_name: str = "openai-compatible"
    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None
    timeout_seconds: float = 30.0


class Settings(BaseModel):
    service_name: str = "animal-gs-agent"
    llm: LLMSettings = LLMSettings()


def get_settings() -> Settings:
    return Settings(
        llm=LLMSettings(
            base_url=os.getenv("ANIMAL_GS_AGENT_LLM_BASE_URL"),
            api_key=os.getenv("ANIMAL_GS_AGENT_LLM_API_KEY"),
            model=os.getenv("ANIMAL_GS_AGENT_LLM_MODEL"),
            timeout_seconds=float(os.getenv("ANIMAL_GS_AGENT_LLM_TIMEOUT_SECONDS", "30")),
        )
    )
