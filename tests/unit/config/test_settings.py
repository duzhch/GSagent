from animal_gs_agent.config import get_settings


def test_get_settings_reads_llm_environment(monkeypatch) -> None:
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_API_KEY", "secret-key")
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_TIMEOUT_SECONDS", "45")

    settings = get_settings()

    assert settings.llm.base_url == "https://api.deepseek.com"
    assert settings.llm.api_key == "secret-key"
    assert settings.llm.model == "deepseek-chat"
    assert settings.llm.timeout_seconds == 45.0
