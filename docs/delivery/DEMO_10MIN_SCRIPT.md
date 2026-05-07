# 10-Minute Demo Script

Goal: clearly show the difference between agent governance and fixed workflow execution.

## Minute 0-2: Startup

1. Activate environment.
2. Export `.env` variables.
3. Run:
   - `bash scripts/native/preflight.sh`
   - `bash scripts/native/start_api.sh`

## Minute 2-4: Agent Understanding

Call:

```bash
curl -sS -X POST http://127.0.0.1:8000/agent/parse-task \
  -H "Content-Type: application/json" \
  -d '{"user_message":"Run genomic selection for BF with sex and batch effects"}' | python -m json.tool
```

Explain:
- Agent extracts trait, goal, fixed effects, and scope.
- Agent does not execute arbitrary shell commands.

## Minute 4-7: Workflow Execution

1. Submit job to `/jobs`.
2. Run job via `/jobs/{id}/run`.
3. Query status `/jobs/{id}`.

Explain:
- Agent stage: dataset checks + routing + validation.
- Workflow stage: fixed GS gold-standard pipeline.

## Minute 7-9: Outputs and Report

1. Call `/jobs/{id}/report`.
2. Call `/jobs/{id}/artifacts`.

Explain:
- Report text explicitly separates Agent layer vs Workflow layer.
- Artifacts expose reproducible output files.

## Minute 9-10: Failure Case

Submit a job with missing trait column and run it.

Show:
- `status=failed`
- `execution_error` and `execution_error_detail`
- `events` timeline with failure event.
