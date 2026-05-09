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

## Install Bundle on Another Host

```bash
cd dist/gsagent-cli-runtime-<timestamp>
bash install_runtime.sh
conda activate gsagent_runtime
```

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
