# GSAgent Singularity/Apptainer Packaging

This package builds a fully bundled `.sif` image:

- `gsagent` CLI
- `nextflow`
- `plink2`
- `Rscript` with required R packages
- Python runtime and project dependencies

No DeepSeek/OpenAI API key is embedded in the image.

## Build

```bash
bash packaging/singularity/build_sif.sh
```

Output:

- `dist/gsagent-runtime-<timestamp>-<gitsha>.sif`

If your cluster requires flags (for example `--fakeroot`), set:

```bash
APPTAINER_BUILD_ARGS="--fakeroot" bash packaging/singularity/build_sif.sh
```

If fakeroot fails with subuid/subgid errors, ask your cluster admin to configure `/etc/subuid` and `/etc/subgid` for your user, or use remote builder:

```bash
singularity remote login
APPTAINER_BUILD_ARGS="--remote" bash packaging/singularity/build_sif.sh
```

## Run

```bash
bash packaging/singularity/run_examples.sh dist/<your-image>.sif /path/to/workdir
```

or manual:

```bash
apptainer exec -B /path/to/workdir:/workspace dist/<your-image>.sif \
  gsagent preflight --workdir /workspace
```

## Runtime Config

Prepare `/path/to/workdir/.env` with secrets and runtime settings:

```bash
ANIMAL_GS_AGENT_API_TOKEN=replace-with-long-random-token
ANIMAL_GS_AGENT_LLM_BASE_URL=https://api.deepseek.com
ANIMAL_GS_AGENT_LLM_API_KEY=replace-with-your-key
ANIMAL_GS_AGENT_LLM_MODEL=deepseek-chat
```

Do not bake API keys into the image.
