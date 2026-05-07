# MVP Acceptance Checklist

Use this list for supervisor/company demo sign-off.

## A. Agent Layer

- [ ] `/agent/parse-task` returns structured task understanding from model API.
- [ ] Job response includes dataset profile and validation flags.
- [ ] Job status includes event timeline (`queued/running/completed/failed`).

## B. Workflow Layer

- [ ] `/jobs/{id}/run` triggers fixed native Nextflow workflow.
- [ ] Workflow failures return stable error codes and detail messages.
- [ ] Successful runs persist `workflow_backend` and `workflow_result_dir`.

## C. Output and Explainability

- [ ] Workflow outputs are parsed into `workflow_summary`.
- [ ] `/jobs/{id}/report` returns agent-facing explanation plus top candidates.
- [ ] `/jobs/{id}/artifacts` lists output files with relative paths and sizes.

## D. Native Delivery

- [ ] `packaging/native/environment.yml` builds environment on user-level conda.
- [ ] `scripts/native/preflight.sh` passes on target cluster.
- [ ] `scripts/native/start_api.sh` launches API.
- [ ] `scripts/native/demo_run.sh` runs full API demo flow.

## E. Verification

- [ ] `pytest tests/unit -q` passes.
- [ ] Development log updated with this release.
- [ ] Latest code pushed to GitHub `main`.
