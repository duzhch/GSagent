from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _test_runtime_defaults(monkeypatch) -> None:
    """Keep legacy tests stable while secure defaults are enabled in app runtime."""
    project_root = Path(__file__).resolve().parents[1]
    monkeypatch.setenv("ANIMAL_GS_AGENT_API_AUTH_DISABLED", "1")
    monkeypatch.setenv(
        "ANIMAL_GS_AGENT_ALLOWED_DATA_ROOTS",
        f"/tmp,{project_root}",
    )
