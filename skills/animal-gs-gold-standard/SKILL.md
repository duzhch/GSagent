---
name: animal-gs-gold-standard
description: Use when working on animal breeding genomic selection workflow design, tool selection, baseline modeling choices, or explaining why the repository uses one-stage GBLUP instead of unsupported alternatives.
---

# Animal GS Gold Standard

## Overview

Use this skill when the repository needs domain-grounded decisions for the animal breeding genomic selection workflow.

The MVP baseline is:

- raw animal phenotypes
- genotype QC with PLINK 2
- fixed-effect aware one-stage GBLUP
- no pedigree-dependent claims

## When To Use

- Choosing the default statistical workflow
- Explaining why the MVP does not claim `ssGBLUP`
- Selecting QC defaults for genotype data
- Grounding design choices in accepted animal breeding tools

## Core Rules

- Use `one-stage GBLUP` as the MVP baseline when pedigree is unavailable
- Use `PLINK 2` for genotype QC
- Treat `BLUPF90+` as the default evaluation engine
- Do not expose arbitrary model choice in the first workflow version
- Do not use `--hwe` as a blind default filter for breeding populations

## References

Read `../../docs/references/animal-gs-gold-standard.md` when you need the citation index and tool links.

