#!/usr/bin/env python
"""Convert pig trait text file into phenotype CSV for agent workflow."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert pig trait TXT to phenotype CSV")
    parser.add_argument("--trait-file", required=True, help="Path to trait txt, e.g. BF.txt")
    parser.add_argument("--trait-name", required=True, help="Trait column name, e.g. BF")
    parser.add_argument("--output", required=True, help="Output CSV path")
    args = parser.parse_args()

    trait_file = Path(args.trait_file)
    output = Path(args.output)

    rows: list[tuple[str, str]] = []
    for line in trait_file.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split()
        if len(parts) < 3:
            continue
        rows.append((parts[0], parts[2]))

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["animal_id", args.trait_name])
        writer.writerows(rows)

    print(f"wrote {len(rows)} rows to {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
