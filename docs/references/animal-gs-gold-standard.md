# Animal GS Gold Standard References

This reference collects the current baseline materials for the repository's animal breeding genomic selection MVP.

## Baseline Statistical Position

For the current MVP:

- genotype data is available
- raw animal phenotype data is available
- pedigree data is not available

Therefore, the repository baseline should be:

- `one-stage GBLUP`
- not `ssGBLUP`

This keeps the MVP statistically honest and technically achievable.

## Fixed Workflow Baseline

The current fixed workflow should follow this order:

1. input validation
2. animal ID alignment
3. phenotype column profiling
4. genotype QC
5. fixed-effect assembly
6. one-stage GBLUP execution
7. evaluation metrics
8. GEBV ranking
9. explanation-oriented output

## Tool Baseline

### PLINK 2

Use for genotype QC:

- `--mind`
- `--geno`
- `--maf`

Avoid treating `--hwe` as a default hard filter in structured breeding populations.

Official reference:
- https://www.cog-genomics.org/plink/2.0/filter

### BLUPF90+

Use as the default evaluation engine for the repository baseline.

Key references:
- Official documentation: https://nce.ads.uga.edu/wiki/doku.php?id=documentation
- Genomic GBLUP tutorial: https://masuday.github.io/blupf90_tutorial/genomic_gblup.html

## Key Literature

### 1. BLUPF90 documentation

- Source: https://nce.ads.uga.edu/wiki/doku.php?id=documentation
- Why it matters:
  - primary documentation for the BLUPF90 toolchain
  - best source for repository-facing integration details

### 2. Masuda genomic GBLUP tutorial

- Source: https://masuday.github.io/blupf90_tutorial/genomic_gblup.html
- Why it matters:
  - concrete implementation notes for genomic GBLUP
  - directly useful for translating the statistical baseline into runnable workflow steps

### 3. Single-step genomic evaluations from theory to practice

- Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC7397237/
- Why it matters:
  - explains where `ssGBLUP` belongs
  - useful to justify why the MVP does not claim single-step support without pedigree

### 4. Genomics in animal breeding

- Source: https://link.springer.com/article/10.1186/s41065-023-00285-w
- Why it matters:
  - broad review for animal breeding genomics context
  - useful for framing the project in presentations and reports

## Design Implications For This Repository

- the workflow layer should not expose arbitrary model choice in MVP
- the agent layer may explain and route, but should not rewrite statistical logic
- workflow adapters should keep tool-specific logic isolated from the API and agent layers

