#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

PHENO="${1:-${ROOT_DIR}/../gs_prototype/data/phenotypes.csv}"
GENO="${2:-${ROOT_DIR}/../gs_prototype/data/genotypes.vcf}"
TRAIT="${3:-grain_yield}"
API_URL="${API_URL:-http://127.0.0.1:8000}"

echo "[demo] health check"
curl -sS "${API_URL}/health" | python -m json.tool

echo "[demo] submit job"
JOB_PAYLOAD=$(cat <<EOF
{
  "user_message": "Run genomic selection for ${TRAIT}",
  "trait_name": "${TRAIT}",
  "phenotype_path": "${PHENO}",
  "genotype_path": "${GENO}"
}
EOF
)

SUBMIT_RESP="$(curl -sS -X POST "${API_URL}/jobs" -H "Content-Type: application/json" -d "${JOB_PAYLOAD}")"
echo "${SUBMIT_RESP}" | python -m json.tool
JOB_ID="$(echo "${SUBMIT_RESP}" | python -c 'import json,sys; print(json.load(sys.stdin)["job_id"])')"

echo "[demo] run job ${JOB_ID}"
curl -sS -X POST "${API_URL}/jobs/${JOB_ID}/run" | python -m json.tool

echo "[demo] report"
curl -sS "${API_URL}/jobs/${JOB_ID}/report" | python -m json.tool

echo "[demo] artifacts"
curl -sS "${API_URL}/jobs/${JOB_ID}/artifacts" | python -m json.tool
