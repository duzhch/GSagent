"""OpenAI-compatible LLM client primitives."""

import json

import httpx

from animal_gs_agent.config import LLMSettings


class OpenAICompatibleLLMClient:
    def __init__(self, settings: LLMSettings, http_client: httpx.Client | None = None) -> None:
        self.settings = settings
        self.http_client = http_client or httpx.Client(timeout=settings.timeout_seconds)

    def build_chat_payload(self, system_prompt: str, user_prompt: str) -> dict:
        return {
            "model": self.settings.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

    def request_json(self, system_prompt: str, user_prompt: str) -> dict:
        response = self.http_client.post(
            f"{self.settings.base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.settings.api_key}",
                "Content-Type": "application/json",
            },
            json=self.build_chat_payload(system_prompt, user_prompt),
        )
        response.raise_for_status()
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        return json.loads(content)
