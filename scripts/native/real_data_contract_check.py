#!/usr/bin/env python
"""Validate real-data contract before workflow execution."""

from __future__ import annotations

import argparse
import json
import sys

from animal_gs_agent.schemas.jobs import JobSubmissionRequest
from animal_gs_agent.services.dataset_profile_service import build_dataset_profile


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate phenotype/genotype contract for animal GS run")
    parser.add_argument("--trait", required=True)
    parser.add_argument("--phenotype-path", required=True)
    parser.add_argument("--genotype-path", required=True)
    args = parser.parse_args()

    payload = JobSubmissionRequest(
        user_message=f"Run genomic selection for {args.trait}",
        trait_name=args.trait,
        phenotype_path=args.phenotype_path,
        genotype_path=args.genotype_path,
    )
    profile = build_dataset_profile(payload)

    print(json.dumps(profile.model_dump(), ensure_ascii=False, indent=2))

    blocking = {
        "phenotype_not_found",
        "genotype_not_found",
        "phenotype_format_unsupported",
        "genotype_format_unsupported",
        "trait_column_missing",
    }
    if any(flag in blocking for flag in profile.validation_flags):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
