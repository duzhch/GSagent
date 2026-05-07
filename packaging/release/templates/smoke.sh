#!/usr/bin/env bash
set -euo pipefail

BUNDLE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_URL="${API_URL:-http://127.0.0.1:8000}"
PHENO="${BUNDLE_ROOT}/assets/data/phenotypes.csv"
GENO="${BUNDLE_ROOT}/assets/data/genotypes.vcf"
TRAIT="${TRAIT:-grain_yield}"
PY="${BUNDLE_ROOT}/runtime_env/bin/python"

"${PY}" - "${API_URL}" "${PHENO}" "${GENO}" "${TRAIT}" <<'PY'
import json
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def request_json(url: str, method: str = "GET", payload: dict | None = None) -> dict:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(url=url, method=method, data=data, headers=headers)
    try:
        with urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        raise RuntimeError(f"{method} {url} failed with {exc.code}: {body}") from exc


api_url, pheno, geno, trait = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

print("[smoke] health")
health = request_json(f"{api_url}/health")
print(json.dumps(health, ensure_ascii=False, indent=2))

print("[smoke] submit")
submit_payload = {
    "user_message": f"Run genomic selection for {trait}",
    "trait_name": trait,
    "phenotype_path": pheno,
    "genotype_path": geno,
}
submitted = request_json(f"{api_url}/jobs", method="POST", payload=submit_payload)
print(json.dumps(submitted, ensure_ascii=False, indent=2))
job_id = submitted["job_id"]

print(f"[smoke] trigger run for {job_id}")
run_resp = request_json(f"{api_url}/jobs/{job_id}/run", method="POST")
print(json.dumps(run_resp, ensure_ascii=False, indent=2))

latest = None
for i in range(1, 121):
    latest = request_json(f"{api_url}/jobs/{job_id}")
    status = latest.get("status", "unknown")
    print(f"[smoke] poll {i}: {status}")
    if status == "completed":
        break
    if status == "failed":
        print("[smoke] job failed")
        print(json.dumps(latest, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    time.sleep(2)
else:
    print("[smoke] timeout waiting for completion")
    print(json.dumps(latest or {}, ensure_ascii=False, indent=2))
    raise SystemExit(1)

print("[smoke] report")
report = request_json(f"{api_url}/jobs/{job_id}/report")
print(json.dumps(report, ensure_ascii=False, indent=2))

print("[smoke] artifacts")
artifacts = request_json(f"{api_url}/jobs/{job_id}/artifacts")
print(json.dumps(artifacts, ensure_ascii=False, indent=2))

print("[smoke] OK")
PY
