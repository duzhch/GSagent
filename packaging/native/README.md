# Native Delivery Package

This directory is the non-container delivery bundle for clusters without Docker or root privileges.

## Quick Start

1. Create environment:
   - `conda env create -f packaging/native/environment.yml`
2. Activate:
   - `conda activate gsagent_native`
3. Configure:
   - `cp packaging/native/.env.example .env`
   - edit `.env` with your API key and workflow paths
4. Preflight:
   - `bash scripts/native/preflight.sh`
5. Start API:
   - `bash scripts/native/start_api.sh`

## Login Node Rule (Slurm-Aware)

Execution policy is controlled by `ANIMAL_GS_AGENT_WORKFLOW_EXECUTION_POLICY`:

- `auto`: on login node, submit to Slurm with `sbatch`; on compute/local node, run native workflow directly
- `slurm`: always submit to Slurm
- `local`: always run local native workflow

When policy uses Slurm submission, set:

- `ANIMAL_GS_AGENT_SLURM_SUBMIT_SCRIPT`

## Included Scripts

- `scripts/native/preflight.sh`: validates runtime dependencies and required paths
- `scripts/native/start_api.sh`: starts FastAPI service with repository-local settings
- `scripts/native/demo_run.sh`: executes a full API demo flow
- `scripts/native/real_data_contract_check.py`: validates phenotype/genotype contract before run
- `scripts/native/prepare_pig_trait_csv.py`: converts pig trait text files into phenotype CSV
