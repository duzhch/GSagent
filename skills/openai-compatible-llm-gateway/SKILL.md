---
name: openai-compatible-llm-gateway
description: Use when adding or modifying model-provider integration for this repository, especially when OpenAI and DeepSeek must share one configuration and one structured-output contract.
---

# OpenAI-Compatible LLM Gateway

## Overview

Use this skill when the repository needs one model gateway that can target multiple OpenAI-compatible providers through configuration.

The first-pass contract is:

- one provider abstraction
- typed structured output
- bounded retries
- fallback parsing

## When To Use

- Adding model-backed task understanding
- Switching between OpenAI and DeepSeek
- Designing structured JSON outputs from the model
- Preventing raw provider logic from leaking into routes or graph nodes

## Core Rules

- Keep provider logic in a dedicated `llm/` package
- Configure only through `base_url`, `api_key`, `model`, and `timeout`
- Validate model output with `Pydantic`
- Fall back to rule parsing on invalid or low-confidence output
- Do not embed provider-specific HTTP details directly inside LangGraph nodes

## References

Read `../../docs/references/openai-compatible-llm-gateway.md` for links and repository-specific constraints.

