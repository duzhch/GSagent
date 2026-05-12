# Animal GS Agent

MVP repository for an animal breeding genomic selection agent.

Chinese documentation: `README_CN.md`

## Goal

Build a LangGraph-based agent that can:

- ingest animal genotype and raw phenotype data
- validate whether the dataset is suitable for a genomic selection run
- launch a fixed one-stage GBLUP workflow
- return ranked GEBV results with breeding-oriented explanations

## MVP Boundary

The first version focuses on:

- raw animal phenotypes
- genotype QC via `PLINK 2`
- fixed-effect aware one-stage `GBLUP`
- agent-guided task understanding, validation, and explanation

The first version does not include:

- pedigree-aware `ssGBLUP`
- free-form workflow generation
- arbitrary tool execution
- multi-tenant production security

## Repository Conventions

- design docs live in `docs/superpowers/specs/`
- implementation plans live in `docs/superpowers/plans/`
- architecture decisions live in `docs/adr/`
- change history lives in `docs/changelog/`

Every meaningful change should be tracked by:

1. a git commit
2. an entry in `docs/changelog/DEVELOPMENT_LOG.md`

## Planned Stack

- `FastAPI` for the service API
- `LangGraph` for agent orchestration
- `PostgreSQL` for job metadata
- `Redis` plus `Celery` for background execution
- `PLINK 2` for genotype QC
- `BLUPF90+` for one-stage GBLUP
- `R` for result shaping and report generation
- `Next.js` for the demo UI
- `Docker Compose` for packaging

## Status

Current MVP includes:

- model-backed task understanding (`/agent/parse-task`)
- job submission and status APIs (`/jobs`, `/jobs/{job_id}`)
- dataset profiling with phenotype header checks and trait-column validation
- runnable job endpoint (`/jobs/{job_id}/run`) that dispatches the fixed native Nextflow workflow, parses output artifacts, and persists structured workflow summaries
- native workflow genotype input support:
  - direct VCF input
  - BED triplet (`.bed/.bim/.fam`) with automatic `plink2` conversion to VCF before workflow execution
- report endpoint (`/jobs/{job_id}/report`) that returns agent-facing explanations with top GEBV candidates
- artifacts endpoint (`/jobs/{job_id}/artifacts`) that returns reproducible output file manifests
- structured execution diagnostics (`execution_error`, `execution_error_detail`) and timeline events (`events`)
- Slurm-aware execution policy for login nodes (auto route to `sbatch` submission)
- optional async queue mode plus worker control plane (`/worker/health`, `/worker/process-once`)

## Native Packaging

For clusters without Docker privileges, use the native delivery bundle:

- `packaging/native/environment.yml`
- `packaging/native/.env.example`
- `scripts/native/preflight.sh`
- `scripts/native/start_api.sh`
- `scripts/native/demo_run.sh`

Runbooks:

- `docs/delivery/REAL_DATA_RUNBOOK.md`
- `docs/delivery/DEMO_10MIN_SCRIPT.md`
- `docs/delivery/MVP_ACCEPTANCE_CHECKLIST.md`

## CLI Software Packaging

The project now exposes a global CLI command: `gsagent`.

### Quick Start (Recommended)

Use this path for new users and test teams. It installs runtime tools and global CLI together.

```bash
bash scripts/install_easy_gsagent.sh
```

What this installer does:

1. install Miniforge automatically when `conda` is missing
2. create/update runtime env with `plink2/nextflow/Rscript`
3. install the project into the runtime env
4. install global `gsagent` launcher to `~/.local/bin`

If `gsagent` is not found after install:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Configure API and Runtime (Interactive)

Run interactive setup in your target workdir:

```bash
gsagent configure --workdir /path/to/project
```

Alias:

```bash
gsagent init --workdir /path/to/project
```

`gsagent configure` writes/updates `/path/to/project/.env` and prompts for:

- LLM base URL
- LLM API key (hidden input)
- LLM model
- API auth token for protected endpoints
- workflow policy and path settings
- allowed data roots whitelist

Important behavior:

- if `.env` already exists, keys are updated in place
- leave API key input empty to keep existing key

### Verify Setup

```bash
gsagent preflight --workdir /path/to/project
gsagent llm-check --workdir /path/to/project --message "health check"
```

Expected:

- `preflight OK`
- `llm-check passed`

### Start Service

```bash
gsagent serve --workdir /path/to/project --host 0.0.0.0 --port 8000 --llm-check auto
```

### API Smoke Test (Copy/Paste)

Open another terminal:

```bash
cd /path/to/project
export GS_TOKEN=$(awk -F= '/^ANIMAL_GS_AGENT_API_TOKEN=/{print $2}' .env)

# Public health endpoint (should be 200)
curl -s http://127.0.0.1:8000/health

# Protected endpoint without token (should be 401)
curl -s http://127.0.0.1:8000/worker/health

# Protected endpoint with token (should be 200)
curl -s -H "X-API-Key: ${GS_TOKEN}" http://127.0.0.1:8000/worker/health
```

### Real Job Smoke Test (BED Input)

```bash
curl -s -X POST "http://127.0.0.1:8000/jobs" \
  -H "X-API-Key: ${GS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "user_message": "Run BF genomic selection with fixed effects sex and batch",
    "trait_name": "BF",
    "phenotype_path": "/path/to/data/BF_phenotype.csv",
    "genotype_path": "/path/to/data/2548bir.bed"
  }'
```

### Cluster Safety Defaults

- `ANIMAL_GS_AGENT_WORKFLOW_EXECUTION_POLICY=auto` prefers Slurm submit when:
  - running on hostnames like `login/head/front/submit/mgmt`, or
  - `sbatch` is available and not inside a `SLURM_JOB_ID` allocation
- `ANIMAL_GS_AGENT_WORKFLOW_PIPELINE_DIR` and `ANIMAL_GS_AGENT_WORKFLOW_OUTPUT_ROOT`
  default to `<workdir>/pipeline` and `<workdir>/runs`

### Security Defaults

- all control-plane/business endpoints require token auth by default:
  - `X-API-Key: <token>` or `Authorization: Bearer <token>`
- `/health` remains public for probes
- job input paths are normalized and constrained to `ANIMAL_GS_AGENT_ALLOWED_DATA_ROOTS`
  - if unset, default root is `ANIMAL_GS_AGENT_WORKDIR`

### Alternative Install Paths (Advanced)

`install_global_gsagent.sh` only installs CLI wrapper and does not install heavy runtime tools
(`plink2`, `nextflow`, `Rscript`):

```bash
bash scripts/install_global_gsagent.sh
```

If you prefer editable Python package install:

```bash
python -m pip install -e .
```

To install full runtime dependencies (recommended for real GS runs):

```bash
conda env create -f packaging/native/environment.yml
conda activate gsagent_native
```

See runtime bundle tooling:

- `packaging/runtime/build_cli_runtime_bundle.sh`
- `packaging/runtime/README.md`

## Offline Release Bundle

To build a zero-download offline package (runtime + app + fixed pipeline + demo data):

```bash
bash packaging/release/build_offline_bundle.sh
```

Output archive is written to `dist/animal-gs-agent-offline-<date>-<gitsha>.tar.gz`.

## Singularity/Apptainer Full Image

Build a full `.sif` image (runtime + tools + app, no API key embedded):

```bash
bash packaging/singularity/build_sif.sh
```

Run examples:

```bash
bash packaging/singularity/run_examples.sh dist/<your-image>.sif /path/to/workdir
```

Details:

- `packaging/singularity/README.md`
