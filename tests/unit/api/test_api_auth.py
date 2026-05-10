import pytest
from fastapi import HTTPException

from animal_gs_agent.api.auth import _extract_token, require_api_token


def test_extract_token_prefers_x_api_key_then_bearer() -> None:
    assert _extract_token(x_api_key="abc", authorization="Bearer xyz") == "abc"
    assert _extract_token(x_api_key=None, authorization="Bearer xyz") == "xyz"
    assert _extract_token(x_api_key=None, authorization=None) == ""


def test_require_api_token_allows_when_auth_disabled(monkeypatch) -> None:
    monkeypatch.setenv("ANIMAL_GS_AGENT_API_AUTH_DISABLED", "1")
    require_api_token(x_api_key=None, authorization=None)


def test_require_api_token_raises_when_token_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("ANIMAL_GS_AGENT_API_AUTH_DISABLED", raising=False)
    monkeypatch.delenv("ANIMAL_GS_AGENT_API_TOKEN", raising=False)

    with pytest.raises(HTTPException) as exc_info:
        require_api_token(x_api_key=None, authorization=None)

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "api auth token is not configured"


def test_require_api_token_raises_on_missing_or_invalid_token(monkeypatch) -> None:
    monkeypatch.delenv("ANIMAL_GS_AGENT_API_AUTH_DISABLED", raising=False)
    monkeypatch.setenv("ANIMAL_GS_AGENT_API_TOKEN", "secret-token")

    with pytest.raises(HTTPException) as missing:
        require_api_token(x_api_key=None, authorization=None)
    assert missing.value.status_code == 401
    assert missing.value.detail == "missing api authentication token"

    with pytest.raises(HTTPException) as invalid:
        require_api_token(x_api_key="wrong-token", authorization=None)
    assert invalid.value.status_code == 401
    assert invalid.value.detail == "invalid api authentication token"

    require_api_token(x_api_key="secret-token", authorization=None)
    require_api_token(x_api_key=None, authorization="Bearer secret-token")
