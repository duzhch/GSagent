"""Application configuration."""

from pydantic import BaseModel


class Settings(BaseModel):
    service_name: str = "animal-gs-agent"


def get_settings() -> Settings:
    return Settings()

