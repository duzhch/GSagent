# Real Data Runbook

This runbook documents one full real-data integration path for animal breeding datasets.

## 1) Prepare Pig Phenotype CSV

Many pig trait files are plain text without headers (example: `data/pig5/BF.txt`).

Convert them first:

```bash
cd /work/home/zyqlab/dzhichao/Agent0428/animal_gs_agent
export PYTHONPATH=src
python scripts/native/prepare_pig_trait_csv.py \
  --trait-file /work/home/zyqlab/dzhichao/Agent0428/data/pig5/BF.txt \
  --trait-name BF \
  --output /work/home/zyqlab/dzhichao/Agent0428/data/pig5/BF_phenotype.csv
```

## 2) Contract Check (Must Pass)

```bash
cd /work/home/zyqlab/dzhichao/Agent0428/animal_gs_agent
export PYTHONPATH=src
python scripts/native/real_data_contract_check.py \
  --trait BF \
  --phenotype-path /work/home/zyqlab/dzhichao/Agent0428/data/pig5/BF_phenotype.csv \
  --genotype-path /work/home/zyqlab/dzhichao/Agent0428/data/pig5/2548bir.bed
```

Expected:
- `phenotype_exists: true`
- `genotype_exists: true`
- `trait_column_present: true`
- no blocking flags in `validation_flags`

## 3) API Submission and Execution

Submit and run through API (`/jobs`, `/jobs/{id}/run`), then inspect:
- `/jobs/{id}`
- `/jobs/{id}/report`
- `/jobs/{id}/artifacts`

## 4) Notes

- Current fixed workflow backend is the Nextflow gold-standard path.
- Native workflow now accepts:
  - VCF input directly
  - BED triplet (`.bed/.bim/.fam`) via automatic PLINK2 conversion to VCF at runtime
- PGEN is still not auto-converted in current version; convert PGEN to VCF manually before submission.
- On login node, set `ANIMAL_GS_AGENT_WORKFLOW_EXECUTION_POLICY=auto` (or `slurm`) so the agent routes execution to Slurm instead of local compute.
