import httpx

from animal_gs_agent.config import LLMSettings
from animal_gs_agent.llm.client import OpenAICompatibleLLMClient


def test_openai_compatible_client_builds_chat_payload() -> None:
    client = OpenAICompatibleLLMClient(
        LLMSettings(
            base_url="https://api.example.com",
            api_key="test-key",
            model="test-model",
        )
    )

    payload = client.build_chat_payload(
        system_prompt="You are a parser.",
        user_prompt="Analyze this breeding request.",
    )

    assert payload["model"] == "test-model"
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1]["role"] == "user"


def test_openai_compatible_client_parses_json_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("https://api.example.com/chat/completions")
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"request_scope":"supported_gs","trait_name":"daily_gain",'
                                '"user_goal":"rank candidates","candidate_fixed_effects":["sex"],'
                                '"population_description":"pig population","missing_inputs":[],"confidence":0.9,'
                                '"clarification_needed":false}'
                            )
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = OpenAICompatibleLLMClient(
        LLMSettings(
            base_url="https://api.example.com",
            api_key="test-key",
            model="test-model",
        ),
        http_client=http_client,
    )

    result = client.request_json(
        system_prompt="You are a parser.",
        user_prompt="Analyze this breeding request.",
    )

    assert result["request_scope"] == "supported_gs"
    assert result["trait_name"] == "daily_gain"
