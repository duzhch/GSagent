# 需求与验收文档导航（研发/测试入口）

## 1. 核心入口

1. 战略与边界：`PRD_HIGH_STANDARD_GS_AGENT.md`
2. 详细需求清单：`REQ_BACKLOG_FILLED.md`
3. 执行流程规范：`ENGINEERING_QA_SOP.md`
4. 需求-测试追踪：`ACCEPTANCE_TRACE_MATRIX.md`

## 2. 研发最小阅读集

1. `PRD_HIGH_STANDARD_GS_AGENT.md`
2. `REQ_BACKLOG_FILLED.md`
3. `ACCEPTANCE_TRACE_MATRIX.md`

研发执行口径：
1. 按 Feature ID 开发。
2. 按 Story ID 提交代码。
3. 按 AC ID 补齐测试证据。

## 3. 测试最小阅读集

1. `REQ_BACKLOG_FILLED.md`
2. `ACCEPTANCE_TRACE_MATRIX.md`
3. `ENGINEERING_QA_SOP.md`

测试执行口径：
1. 对 AC 逐条验证。
2. 对风险分支单独验证。
3. 结果回填追踪矩阵状态与证据。

## 4. 审核最小阅读集（你本人）

1. `PRD_HIGH_STANDARD_GS_AGENT.md`：看方向是否偏离
2. `REQ_BACKLOG_FILLED.md`：看需求是否可执行
3. `ACCEPTANCE_TRACE_MATRIX.md`：看证据是否闭环
4. `ENGINEERING_QA_SOP.md`：看流程是否被遵循

## 5. 版本管理规则

1. 所有需求变更先改 `REQ_BACKLOG_FILLED.md` 再开发。
2. 每次 PR 必须更新 `ACCEPTANCE_TRACE_MATRIX.md`。
3. 每次验收会后更新 Feature 状态（`ready/in_dev/in_test/accepted/blocked`）。

