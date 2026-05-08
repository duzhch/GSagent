# 需求-测试-验收追踪矩阵

## 1. 说明

本矩阵用于把需求ID、验收标准ID、测试用例ID、证据文件统一关联。  
每个发布版本都要更新本文件，作为最终审核依据。

字段定义：

- Req ID：Feature ID
- AC ID：验收标准编号
- Test Case ID：测试用例编号
- Test Type：UT / IT / E2E / Risk
- Evidence：测试报告或日志路径
- Owner：责任人
- Coverage Status：`TBD` / `IN_PROGRESS` / `PASS` / `FAIL`

## 2. P0 追踪矩阵

| Req ID | AC ID | Test Case ID | Test Type | Evidence | Owner | Coverage Status |
|---|---|---|---|---|---|---|
| `F-P0-01-01` | `AC-P0-01-01` | `TC-P0-01-01` | IT | `tests/integration/p0_supervisor_flow.md` | Dev+QA | IN_PROGRESS |
| `F-P0-01-01` | `AC-P0-01-02` | `TC-P0-01-02` | Risk | `tests/risk/p0_retry_escalation.md` | Dev+QA | IN_PROGRESS |
| `F-P0-01-01` | `AC-P0-01-03` | `TC-P0-01-03` | E2E | `tests/e2e/p0_trace_visibility.md` | Dev+QA | IN_PROGRESS |
| `F-P0-01-02` | `AC-P0-01-04` | `TC-P0-01-04` | UT | `tests/unit/p0_trace_schema_test.py` | Dev | PASS |
| `F-P0-01-02` | `AC-P0-01-05` | `TC-P0-01-05` | IT | `tests/integration/p0_trace_linkage.md` | Dev+QA | PASS |
| `F-P0-02-01` | `AC-P0-02-01` | `TC-P0-02-01` | UT | `tests/unit/p0_qc_missingness_test.py` | Dev | TBD |
| `F-P0-02-01` | `AC-P0-02-02` | `TC-P0-02-02` | E2E | `tests/e2e/p0_qc_blocking.md` | QA | TBD |
| `F-P0-02-01` | `AC-P0-02-03` | `TC-P0-02-03` | Risk | `tests/risk/p0_override_audit.md` | QA | TBD |
| `F-P0-02-02` | `AC-P0-02-04` | `TC-P0-02-04` | IT | `tests/integration/p0_population_structure.md` | Dev+QA | TBD |
| `F-P0-02-02` | `AC-P0-02-05` | `TC-P0-02-05` | Risk | `tests/risk/p0_structure_risk_tag.md` | QA | TBD |
| `F-P0-02-03` | `AC-P0-02-06` | `TC-P0-02-06` | IT | `tests/integration/p0_pheno_batch_diagnosis.md` | Dev+QA | TBD |
| `F-P0-02-03` | `AC-P0-02-07` | `TC-P0-02-07` | E2E | `tests/e2e/p0_covariate_recommendation.md` | QA | TBD |
| `F-P0-03-01` | `AC-P0-03-01` | `TC-P0-03-01` | UT | `tests/unit/p0_model_pool_availability.py` | Dev | TBD |
| `F-P0-03-01` | `AC-P0-03-02` | `TC-P0-03-02` | IT | `tests/integration/p0_model_pool_rejection_reason.md` | QA | TBD |
| `F-P0-03-02` | `AC-P0-03-03` | `TC-P0-03-03` | UT | `tests/unit/p0_trial_budget_guard.py` | Dev | TBD |
| `F-P0-03-02` | `AC-P0-03-04` | `TC-P0-03-04` | E2E | `tests/e2e/p0_early_stop_reason.md` | QA | TBD |
| `F-P0-03-02` | `AC-P0-03-05` | `TC-P0-03-05` | Risk | `tests/risk/p0_reproducibility_seed.md` | QA | TBD |
| `F-P0-03-03` | `AC-P0-03-06` | `TC-P0-03-06` | IT | `tests/integration/p0_within_pop_protocol.md` | Dev+QA | TBD |
| `F-P0-03-03` | `AC-P0-03-07` | `TC-P0-03-07` | IT | `tests/integration/p0_cross_pop_protocol.md` | Dev+QA | TBD |
| `F-P0-04-01` | `AC-P0-04-01` | `TC-P0-04-01` | UT | `tests/unit/p0_claim_evidence_map.py` | Dev | TBD |
| `F-P0-04-01` | `AC-P0-04-02` | `TC-P0-04-02` | Risk | `tests/risk/p0_reject_no_evidence.md` | QA | TBD |
| `F-P0-04-02` | `AC-P0-04-03` | `TC-P0-04-03` | IT | `tests/integration/p0_leakage_check.md` | QA | TBD |
| `F-P0-04-02` | `AC-P0-04-04` | `TC-P0-04-04` | IT | `tests/integration/p0_metric_consistency.md` | QA | TBD |
| `F-P0-05-01` | `AC-P0-05-01` | `TC-P0-05-01` | UT | `tests/unit/p0_metric_pearson_rmse.py` | Dev | TBD |
| `F-P0-05-01` | `AC-P0-05-02` | `TC-P0-05-02` | IT | `tests/integration/p0_metric_aggregation.md` | QA | TBD |
| `F-P0-05-02` | `AC-P0-05-03` | `TC-P0-05-03` | IT | `tests/integration/p0_top1_regret.md` | Dev+QA | TBD |
| `F-P0-05-02` | `AC-P0-05-04` | `TC-P0-05-04` | Risk | `tests/risk/p0_oracle_missing.md` | QA | TBD |
| `F-P0-05-03` | `AC-P0-05-05` | `TC-P0-05-05` | IT | `tests/integration/p0_trials_to_95.md` | Dev+QA | TBD |
| `F-P0-05-03` | `AC-P0-05-06` | `TC-P0-05-06` | IT | `tests/integration/p0_invalid_trial_rate.md` | QA | TBD |

## 3. P1 追踪矩阵

| Req ID | AC ID | Test Case ID | Test Type | Evidence | Owner | Coverage Status |
|---|---|---|---|---|---|---|
| `F-P1-01-01` | `AC-P1-01-01` | `TC-P1-01-01` | IT | `tests/integration/p1_knowledge_connector.md` | Dev+QA | TBD |
| `F-P1-01-02` | `AC-P1-01-02` | `TC-P1-01-02` | IT | `tests/integration/p1_retrieval_rerank.md` | QA | TBD |
| `F-P1-01-03` | `AC-P1-01-03` | `TC-P1-01-03` | Risk | `tests/risk/p1_evidence_conflict.md` | QA | TBD |
| `F-P1-02-01` | `AC-P1-02-01` | `TC-P1-02-01` | UT | `tests/unit/p1_badcase_schema.py` | Dev | TBD |
| `F-P1-02-02` | `AC-P1-02-02` | `TC-P1-02-02` | IT | `tests/integration/p1_badcase_similarity.md` | QA | TBD |
| `F-P1-02-03` | `AC-P1-02-03` | `TC-P1-02-03` | E2E | `tests/e2e/p1_preventive_actions.md` | QA | TBD |
| `F-P1-03-01` | `AC-P1-03-01` | `TC-P1-03-01` | IT | `tests/integration/p1_technical_report.md` | Dev+QA | TBD |
| `F-P1-03-02` | `AC-P1-03-02` | `TC-P1-03-02` | IT | `tests/integration/p1_decision_report.md` | QA | TBD |
| `F-P1-03-03` | `AC-P1-03-03` | `TC-P1-03-03` | IT | `tests/integration/p1_management_report.md` | QA | TBD |
| `F-P1-04-01` | `AC-P1-04-01` | `TC-P1-04-01` | Risk | `tests/risk/p1_approval_gate.md` | Dev+QA | IN_PROGRESS |
| `F-P1-04-02` | `AC-P1-04-02` | `TC-P1-04-02` | IT | `tests/integration/p1_override_log.md` | Dev+QA | IN_PROGRESS |
| `F-P1-04-03` | `AC-P1-04-03` | `TC-P1-04-03` | E2E | `tests/e2e/p1_abort_and_fallback.md` | QA | TBD |

## 4. P2 追踪矩阵

| Req ID | AC ID | Test Case ID | Test Type | Evidence | Owner | Coverage Status |
|---|---|---|---|---|---|---|
| `F-P2-01-01` | `AC-P2-01-01` | `TC-P2-01-01` | IT | `tests/integration/p2_baseline_bench.md` | Dev+QA | TBD |
| `F-P2-01-02` | `AC-P2-01-02` | `TC-P2-01-02` | IT | `tests/integration/p2_ablation_bench.md` | QA | TBD |
| `F-P2-01-03` | `AC-P2-01-03` | `TC-P2-01-03` | E2E | `tests/e2e/p2_plot_export.md` | QA | TBD |
| `F-P2-02-01` | `AC-P2-02-01` | `TC-P2-02-01` | UT | `tests/unit/p2_failure_classifier.py` | Dev | TBD |
| `F-P2-02-02` | `AC-P2-02-02` | `TC-P2-02-02` | IT | `tests/integration/p2_retry_policy.md` | QA | TBD |
| `F-P2-02-03` | `AC-P2-02-03` | `TC-P2-02-03` | Risk | `tests/risk/p2_escalation_stop.md` | QA | TBD |
| `F-P2-03-01` | `AC-P2-03-01` | `TC-P2-03-01` | IT | `tests/integration/p2_authz_scope.md` | Dev+QA | TBD |
| `F-P2-03-02` | `AC-P2-03-02` | `TC-P2-03-02` | IT | `tests/integration/p2_quota_control.md` | QA | TBD |
| `F-P2-03-03` | `AC-P2-03-03` | `TC-P2-03-03` | E2E | `tests/e2e/p2_observability_audit.md` | QA | TBD |

## 5. 更新规则

1. Dev 开始实现某 Feature 时，将对应行状态改为 `IN_PROGRESS`。
2. QA 完成测试并确认通过后，将状态改为 `PASS` 并填写证据路径。
3. 若失败，状态改为 `FAIL`，并在 PR 评论中附 root cause 与修复计划。
4. 发布评审时，P0 范围内不得存在 `TBD` 或 `FAIL`。
