# OpenAI-Compatible LLM Gateway References

This reference defines the repository's first-pass model integration pattern.

## Integration Policy

Use a unified provider abstraction based on:

- `base_url`
- `api_key`
- `model`
- `timeout`

The repository should not hard-code OpenAI-specific or DeepSeek-specific logic into FastAPI routes or LangGraph nodes.

## Current Recommended API Style

Use an OpenAI-compatible chat completions style integration for the first pass.

Why:

- DeepSeek documents OpenAI-compatible API usage
- OpenAI-compatible request shape is the easiest shared denominator
- it supports rapid multi-provider switching through configuration

## Provider References

### OpenAI

- Chat Completions API reference:
  - https://platform.openai.com/docs/api-reference/chat
- Structured outputs guide:
  - https://platform.openai.com/docs/guides/structured-outputs

### DeepSeek

- API documentation:
  - https://api-docs.deepseek.com/

## Repository Contract

The model output for task understanding should be validated against a typed schema.

Expected fields:

- `request_scope`
- `trait_name`
- `user_goal`
- `candidate_fixed_effects`
- `population_description`
- `missing_inputs`
- `confidence`
- `clarification_needed`

## Failure Handling Policy

If the provider call fails or returns unusable output:

1. retry only inside a bounded limit
2. validate with `Pydantic`
3. fall back to rule-based parsing
4. mark the request for clarification when needed

## Design Implications For This Repository

- keep provider logic in a dedicated `llm/` package
- keep prompt templates separate from HTTP transport details
- keep agent nodes focused on state transitions, not raw HTTP

