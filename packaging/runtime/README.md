# GSAgent CLI Runtime Packaging

This directory packages the project as a reusable command-line tool (`gsagent`) plus a baseline runtime environment.

## What It Produces

- Python wheel for `animal-gs-agent` with console entrypoint:
  - `gsagent`
- Runtime environment template:
  - `environment.yml`
- Installer script:
  - `install_runtime.sh`

## Build Bundle

```bash
bash packaging/runtime/build_cli_runtime_bundle.sh
```

Output (default):

- `dist/gsagent-cli-runtime-<timestamp>/`

## Global Command Install (Current Repo)

Foolproof installer (recommended):

```bash
bash scripts/install_easy_gsagent.sh
```

This mode installs both runtime dependencies and the global launcher.

Minimal launcher-only mode:

```bash
bash scripts/install_global_gsagent.sh
```

This writes `gsagent` to `~/.local/bin/gsagent`.

## Install Bundle on Another Host

```bash
cd dist/gsagent-cli-runtime-<timestamp>
bash install_runtime.sh
conda activate gsagent_runtime
```

`install_runtime.sh` now verifies that these tools are available in the created env:

- `nextflow`
- `plink2`
- `Rscript` (with `jsonlite`)

## Typical Usage

From any directory:

```bash
gsagent preflight --workdir /path/to/project
gsagent llm-check --workdir /path/to/project
gsagent serve --workdir /path/to/project --host 0.0.0.0 --port 8000
gsagent worker --workdir /path/to/project
```

`--workdir` lets you invoke the software globally while binding runtime context to a target folder (env file, output paths, local configs).

At API startup, `gsagent serve` can run an interactive LLM availability check and ask user input for probe message and missing config values.

## Security Defaults

Set these in the target workdir `.env`:

```bash
ANIMAL_GS_AGENT_API_TOKEN=replace-with-long-random-token
ANIMAL_GS_AGENT_ALLOWED_DATA_ROOTS=/data/projectA,/data/shared
```

- Protected endpoints require `X-API-Key` or `Authorization: Bearer`.
- `/health` stays open for liveness checks.
- Job input paths are constrained to allowed roots; when unset it falls back to `ANIMAL_GS_AGENT_WORKDIR`.

## Cluster Execution Defaults

- `ANIMAL_GS_AGENT_WORKFLOW_EXECUTION_POLICY=auto` prefers Slurm submission on head/login-like nodes and on nodes where `sbatch` exists outside active Slurm allocations.
- Default pipeline/output roots are workdir-scoped:
  - `<workdir>/pipeline`
  - `<workdir>/runs`
