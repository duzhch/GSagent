# Animal GS Agent Offline Bundle

This bundle is designed for zero-download startup on a new Linux server.

## What is included

- prepacked Python+R runtime (`runtime_env.tar.gz`)
- application source (`app/`)
- fixed GS gold-standard pipeline (`assets/pipeline/`)
- demo data (`assets/data/`)
- start/stop/smoke scripts

## Quick start

1. Start API + worker:
   - `bash start_all.sh`
2. Run smoke test:
   - `bash smoke.sh`
3. Stop services:
   - `bash stop_all.sh`

Default API URL is `http://127.0.0.1:8000`.

## Optional LLM provider

No LLM key is required for baseline run. The service falls back to local heuristic task parsing when no LLM config is present.

To enable model-backed parsing, create `.env` from `.env.example` and fill:

- `ANIMAL_GS_AGENT_LLM_BASE_URL`
- `ANIMAL_GS_AGENT_LLM_API_KEY`
- `ANIMAL_GS_AGENT_LLM_MODEL`

Then restart with `bash stop_all.sh && bash start_all.sh`.
