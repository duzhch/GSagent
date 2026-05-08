# P2 Ablation Benchmark Integration Evidence

## Scope

- Req: `F-P2-01-02`
- AC: `AC-P2-01-02`
- Goal: verify ablation benchmark emits delta metrics and impact labels.

## Command

```bash
pytest -q tests/unit/p2_benchmark_service.py::test_ablation_benchmark_outputs_delta_effects
```

## Result

- PASS (`1 passed`)
- Ablation output includes multiple controlled removals.
- Each ablation contains:
  - `delta_pearson`
  - `delta_rmse`
  - impact level (`minor|moderate|major`)
