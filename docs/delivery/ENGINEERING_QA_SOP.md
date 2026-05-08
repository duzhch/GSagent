# 研发与测试执行SOP（GS Hardness）

## 1. 目的

定义从需求评审到验收发布的统一流程，解决“需求理解不一致、验收口径不一致、证据不完整”的管理问题。

## 2. 角色与职责（RACI）

| 环节 | PM | Tech Lead | Dev | QA | Reviewer |
|---|---|---|---|---|---|
| 需求定义与优先级 | A | C | I | I | I |
| 技术方案评审 | C | A | R | C | C |
| 开发实现 | I | C | A/R | I | I |
| 测试设计与执行 | I | C | C | A/R | I |
| 验收签收 | A | C | C | R | C |

说明：A=最终负责，R=执行，C=协作，I=知会。

## 3. 文档阅读入口（研发与测试必须遵循）

## 3.1 研发阅读顺序

1. 产品目标与边界：`PRD_HIGH_STANDARD_GS_AGENT.md`
2. 具体需求与验收标准：`REQ_BACKLOG_FILLED.md`
3. 需求-测试映射：`ACCEPTANCE_TRACE_MATRIX.md`
4. 当前架构快照：`AGENT_FULL_PICTURE.md`

## 3.2 测试阅读顺序

1. 具体验收标准：`REQ_BACKLOG_FILLED.md`
2. 追踪矩阵与用例范围：`ACCEPTANCE_TRACE_MATRIX.md`
3. 环境与运行脚本：`REAL_DATA_RUNBOOK.md`、`MVP_ACCEPTANCE_CHECKLIST.md`
4. 现有接口与行为：`AGENT_FULL_PICTURE.md`

## 4. 工作流状态机（需求到发布）

1. `draft`：PM 完成需求草案
2. `ready`：Tech Lead + QA 确认可开发可测试
3. `in_dev`：开发实现中
4. `in_test`：测试执行中
5. `accepted`：验收通过
6. `blocked`：依赖或质量问题阻断

禁止跳步：`draft -> accepted`。

## 5. 标准执行流程

## 5.1 需求冻结

输入：Feature 条目与 AC。  
输出：需求状态切换为 `ready`。

准入条件：
1. Feature ID、Story ID、AC ID 已编号。
2. 输入输出契约明确。
3. 失败回退策略明确。

## 5.2 开发阶段

开发必须执行：
1. PR 标题与描述包含 Feature ID（例如 `F-P0-03-02`）。
2. 提交信息包含 Story ID。
3. 代码中新增结构化日志字段：`task_id`, `feature_id`, `agent_id`, `decision_id`。
4. 同步更新 `ACCEPTANCE_TRACE_MATRIX.md` 对应行的实现状态。

## 5.3 测试阶段

测试必须执行：
1. 单元测试：验证核心逻辑与边界条件。
2. 集成测试：验证跨模块契约。
3. E2E 测试：验证完整业务链路。
4. 风险测试：验证失败回退与审批分支。

测试输出必须包含：
1. 测试报告（通过率、失败项、阻断项）。
2. 关键日志与产物证据（json/csv/report）。
3. 对应 AC 的逐条结果。

## 5.4 验收阶段

验收由 PM 主持，QA 给结果，Tech Lead 给技术意见。  
通过条件（全部满足）：
1. Feature 所有 AC 通过。
2. 追踪矩阵中 `Coverage Status=PASS`。
3. 回归不破坏 P0 已通过能力。
4. 文档更新完整。

## 6. Definition of Ready（DoR）

Feature 进入开发前必须满足：
1. ID、优先级、业务目标已定义。
2. 输入输出 schema 已定义。
3. AC 至少包含：正常、异常、回退三类。
4. 指标影响定义明确（至少一个可量化指标）。

## 7. Definition of Done（DoD）

Feature 完成必须满足：
1. 代码合并标准通过。
2. 单元+集成+E2E 测试证据完整。
3. 追踪矩阵更新为 PASS。
4. 使用文档与运维说明已更新。

## 8. 变更管理规范

需求变更触发条件：
1. 数据或场景新增导致原 AC 不再适用。
2. 研究目标新增评测指标。
3. 安全/合规要求更新。

变更流程：
1. PM 提交变更单（变更内容、影响范围、风险）。
2. Tech Lead/QA 评审变更影响。
3. 更新 `REQ_BACKLOG_FILLED.md` 与 `ACCEPTANCE_TRACE_MATRIX.md`。
4. 重新冻结相关 Feature。

## 9. 验收会议模板

会议输入：
1. Feature 列表及状态
2. AC 测试结果
3. 阻断项与风险清单

会议输出：
1. 通过/驳回结论
2. 未通过项整改清单
3. 下一批进入 `ready` 的 Feature

## 10. 发布门禁（Release Gate）

发布前必须满足：
1. 所有纳入范围的 P0/P1 Feature 为 `accepted`。
2. 无 P0 blocker。
3. 关键指标不劣化（由 QA 报告给出）。
4. 离线包或部署流程可复现演示通过。

