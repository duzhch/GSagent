# GS Hardness 需求清单（已填充）

## 1. 文档目的

本文件是 `PRD_HIGH_STANDARD_GS_AGENT.md` 的执行化版本，供研发、测试、产品统一使用。  
目标：把战略目标落成可开发、可测试、可验收、可追踪的需求清单。

## 2. Program Card（项目总卡）

| 字段 | 内容 |
|---|---|
| Program ID | `PRG-GS-HARDNESS-001` |
| Program Name | 面向科研与育种从业者的高标准 GS 智能体 |
| Problem Statement | 现有系统偏 workflow 服务，缺乏智能决策、审计、记忆和可量化收益 |
| Business Goal | 降低用户决策成本，减少无效试验，提高结果置信度并形成可发表评测体系 |
| User Segment | 科研人员、育种算法团队、数据平台主管 |
| North Star | 在预算约束下实现更低 Regret 与更低无效试验率 |
| Guardrail | 结果可追溯率 100%，高风险任务必须有审计结论 |
| In Scope | 多智能体编排、深度QC、模型策略、审计、指标面板、知识与记忆闭环 |
| Out of Scope | 通用聊天、任意脚本执行、无边界自治 |

## 3. Epic 清单（按优先级）

| Epic ID | 名称 | 优先级 | 目标 |
|---|---|---|---|
| `E-P0-01` | 总控智能体编排 | P0 | 从单流程升级为可解释多智能体决策流 |
| `E-P0-02` | 数据智能体深度QC | P0 | 数据风险前置阻断，降低无效试验 |
| `E-P0-03` | 模型智能体策略搜索 | P0 | 预算约束下自动选择更优模型与配置 |
| `E-P0-04` | 审计智能体 | P0 | 结论可审计、可反证、可追责 |
| `E-P0-05` | 指标体系产品化 | P0 | 论文评测指标内建化 |
| `E-P1-01` | 知识智能体（RAG） | P1 | 证据驱动决策，减少经验依赖 |
| `E-P1-02` | Badcase 记忆闭环 | P1 | 失败可学习，重复错误下降 |
| `E-P1-03` | 多角色报告 | P1 | 技术/决策/管理多视角输出 |
| `E-P1-04` | 人机协同控制点 | P1 | 在高风险点引入人工审批 |
| `E-P2-01` | 对比与消融实验台 | P2 | 论文级方法评估自动化 |
| `E-P2-02` | Debug 智能体 | P2 | 自动失败诊断与受控重试 |
| `E-P2-03` | 平台化治理能力 | P2 | 团队可运营、可权限管理 |

## 4. Feature Backlog（完整填充）

## 4.1 E-P0-01 总控智能体编排

### Feature: `F-P0-01-01` 多智能体状态图运行时

| 字段 | 内容 |
|---|---|
| User Scenario | 用户提交任务后，系统自动执行“数据->模型->审计->报告”分工流程 |
| Trigger | `POST /jobs` + `run` |
| Input Contract | 任务定义（群体、性状、场景、预算、候选池） |
| Output Contract | `decision_trace.json`、子智能体中间产物、最终决策结果 |
| LLM Role | 任务拆解、分支选择、失败回退策略建议 |
| Non-LLM Role | 状态机调度、任务锁、重试计数、超时控制 |

Acceptance Criteria:
1. Given 合法任务，When 执行总控图，Then 必须按配置路径产出完整决策轨迹。
2. Given 子智能体失败，When 超过重试阈值，Then 进入人工升级状态并停止盲重试。
3. Given 任务完成，When 查看任务详情，Then 可看到每个节点的输入、输出、耗时、状态。

### Feature: `F-P0-01-02` 决策轨迹标准化

| 字段 | 内容 |
|---|---|
| User Scenario | 研发和审计人员需要回放每次决策依据 |
| Trigger | 任意任务执行完成或失败 |
| Output Contract | 标准化 `decision_trace`（节点、动作、证据、置信度、反事实） |

Acceptance Criteria:
1. Given 任意任务，When 导出 trace，Then 字段完整且通过 schema 校验。
2. Given 审计请求，When 检查关键结论，Then 必须能定位其来源节点与证据链接。

Story 清单:
- `S-P0-01-01` 状态图节点协议定义
- `S-P0-01-02` 节点执行器与重试策略
- `S-P0-01-03` trace schema 与持久化
- `S-P0-01-04` trace 可视化 API

## 4.2 E-P0-02 数据智能体深度QC

### Feature: `F-P0-02-01` 基因型QC扩展

| 字段 | 内容 |
|---|---|
| User Scenario | 用户上传不同质量数据，系统自动判定是否可继续 |
| Trigger | 模型执行前 |
| Input Contract | 基因型文件（VCF/BED/PGEN） |
| Output Contract | 缺失率、MAF、样本过滤建议、风险等级 |

Acceptance Criteria:
1. Given 原始基因型，When QC完成，Then 输出样本与位点级缺失率统计。
2. Given 低质量数据，When 风险等级为高，Then 默认阻断后续模型执行。
3. Given 阻断结果，When 用户人工 override，Then 审计日志必须记录审批人和原因。

### Feature: `F-P0-02-02` 群体结构与异常样本分析

| 字段 | 内容 |
|---|---|
| User Scenario | 研究人员希望提前识别群体偏差对结果的影响 |
| Output Contract | PCA 坐标、离群样本列表、近亲关系告警 |

Acceptance Criteria:
1. Given 群体数据，When 执行结构分析，Then 产出 PCA 与离群样本清单。
2. Given 存在显著结构偏差，When 进入模型阶段，Then 系统必须携带风险标签。

### Feature: `F-P0-02-03` 表型异常与批次效应诊断

| 字段 | 内容 |
|---|---|
| User Scenario | 用户需要识别异常值和批次偏差，避免误导预测 |
| Output Contract | 异常值比例、批次效应显著性、处理建议 |

Acceptance Criteria:
1. Given 表型表，When 诊断完成，Then 产出异常值与批次效应报告。
2. Given 批次效应显著，When 生成模型计划，Then 必须推荐协变量或分层策略。

Story 清单:
- `S-P0-02-01` QC 指标 schema
- `S-P0-02-02` PLINK2 QC 执行器
- `S-P0-02-03` PCA/relatedness 模块
- `S-P0-02-04` phenotype outlier/batch 模块
- `S-P0-02-05` 风险分级与阻断策略

## 4.3 E-P0-03 模型智能体策略搜索

### Feature: `F-P0-03-01` 候选模型池管理

| 字段 | 内容 |
|---|---|
| User Scenario | 同一任务支持多候选模型统一比较 |
| Candidate Pool | GBLUP、BayesB、XGBoost |
| Output Contract | 模型候选列表、可用性、前置条件 |

Acceptance Criteria:
1. Given 任务定义，When 初始化模型池，Then 返回可执行模型集合和禁用原因。
2. Given 数据不满足某模型要求，When 规划执行，Then 必须标明不可用理由。

### Feature: `F-P0-03-02` 预算约束下策略搜索

| 字段 | 内容 |
|---|---|
| User Scenario | 用户给出试验预算，系统自动搜索接近最优方案 |
| Input Contract | `max_trials`, 场景类型, 协变量空间 |
| Output Contract | trial 序列、选中方案、消耗预算、终止原因 |

Acceptance Criteria:
1. Given `max_trials=N`，When 搜索执行，Then trial 总数不得超过 N。
2. Given 早停条件触发，When 停止搜索，Then 输出停止依据和当前最优解。
3. Given 同输入同随机种子，When 重跑，Then trial 序列与结论可复现。

### Feature: `F-P0-03-03` 场景化验证协议

| 字段 | 内容 |
|---|---|
| User Scenario | 支持群体内与跨群体两种预测场景 |
| Output Contract | 按场景的训练/验证拆分记录与指标 |

Acceptance Criteria:
1. Given within-pop 任务，When 评估，Then 输出 within-pop 指标。
2. Given cross-pop 任务，When 评估，Then 输出跨群体泛化指标。

Story 清单:
- `S-P0-03-01` 模型注册表
- `S-P0-03-02` trial orchestrator
- `S-P0-03-03` 协变量搜索器
- `S-P0-03-04` 场景化 split 协议
- `S-P0-03-05` reproducibility seed 策略

## 4.4 E-P0-04 审计智能体

### Feature: `F-P0-04-01` 结论证据链审计

| 字段 | 内容 |
|---|---|
| User Scenario | 用户需要知道每条结论依据是什么 |
| Output Contract | claim-evidence map, 审计结论 |

Acceptance Criteria:
1. Given 报告结论，When 审计，Then 每条结论必须绑定证据链接。
2. Given 无证据结论，When 审计，Then 标记 `reject`。

### Feature: `F-P0-04-02` 泄漏与口径一致性审计

| 字段 | 内容 |
|---|---|
| User Scenario | 防止数据泄漏或指标计算错误 |
| Output Contract | leakage check、metric check、风险标签 |

Acceptance Criteria:
1. Given 训练验证划分，When 审计，Then 输出是否存在泄漏风险。
2. Given 指标报告，When 审计，Then 口径不一致必须报警。

Story 清单:
- `S-P0-04-01` 审计规则 DSL
- `S-P0-04-02` claim-evidence validator
- `S-P0-04-03` leakage checker
- `S-P0-04-04` 审计 verdict API

## 4.5 E-P0-05 指标体系产品化

### Feature: `F-P0-05-01` 性能指标统一计算

| 字段 | 内容 |
|---|---|
| 指标 | Pearson, RMSE |
| 输出 | task-level 与 aggregate-level |

Acceptance Criteria:
1. Given 任意 trial，When 评估，Then 必须输出 Pearson 和 RMSE。
2. Given 多 trial，When 聚合，Then 输出分组统计（群体/性状/模型）。

### Feature: `F-P0-05-02` 决策质量指标

| 字段 | 内容 |
|---|---|
| 指标 | Top-1 命中率, Regret（对 Oracle-best） |

Acceptance Criteria:
1. Given 任务完成，When 计算决策质量，Then 输出 Top-1 与 Regret。
2. Given Oracle 缺失，When 评估，Then 返回可解释的不可计算原因。

### Feature: `F-P0-05-03` 搜索效率指标

| 字段 | 内容 |
|---|---|
| 指标 | Trials-to-95%-Best, Invalid Trial Rate |

Acceptance Criteria:
1. Given 搜索记录，When 评估，Then 输出达到 95% 最优所需 trial 数。
2. Given 失败 trial，When 统计，Then 输出无效试验率并可下钻原因。

Story 清单:
- `S-P0-05-01` metric schema
- `S-P0-05-02` oracle comparator
- `S-P0-05-03` efficiency analyzer
- `S-P0-05-04` metrics dashboard API

## 4.6 E-P1-01 知识智能体（RAG）

Features:
- `F-P1-01-01` 知识源接入（历史任务、SOP、文献）
- `F-P1-01-02` 检索与重排序
- `F-P1-01-03` 证据引用与冲突标注

核心 AC:
1. 关键建议必须附至少 1 条证据。
2. 证据冲突时必须显示冲突说明，不得静默覆盖。

Story:
- `S-P1-01-01` knowledge connector
- `S-P1-01-02` retrieval API
- `S-P1-01-03` citation formatter

## 4.7 E-P1-02 Badcase 记忆闭环

Features:
- `F-P1-02-01` badcase 入库标准化
- `F-P1-02-02` 相似任务检索与预警
- `F-P1-02-03` 避险策略推荐

核心 AC:
1. 新任务执行前必须查询历史 badcase。
2. 若命中高相似 badcase，必须输出规避动作。

Story:
- `S-P1-02-01` badcase schema
- `S-P1-02-02` similarity search
- `S-P1-02-03` prevent-action generator

## 4.8 E-P1-03 多角色报告

Features:
- `F-P1-03-01` 技术报告模板
- `F-P1-03-02` 决策报告模板
- `F-P1-03-03` 管理报告模板

核心 AC:
1. 同任务三类报告结论一致，不一致需给解释。
2. 报告包含审计结论和风险提示。

## 4.9 E-P1-04 人机协同控制点

Features:
- `F-P1-04-01` 高风险审批节点
- `F-P1-04-02` override 审计记录
- `F-P1-04-03` 强制中止与回退

核心 AC:
1. 高风险任务未审批不得执行。
2. override 必须记录责任人、原因、时间戳。

## 4.10 E-P2-01 对比与消融实验台

Features:
- `F-P2-01-01` 基线实验编排（single/react/multi-agent）
- `F-P2-01-02` 消融实验编排
- `F-P2-01-03` 图表自动导出

核心 AC:
1. 一键运行可输出对比表与关键图。
2. 每次实验结果可复现并带版本信息。

## 4.11 E-P2-02 Debug 智能体

Features:
- `F-P2-02-01` 失败分类（环境/数据/代码/资源）
- `F-P2-02-02` 修复建议与重试策略
- `F-P2-02-03` 超限升级人工

核心 AC:
1. 失败任务必须落分类，不得“unknown”无解释结束。
2. 超过重试阈值必须升级人工并停止自动重试。

## 4.12 E-P2-03 平台化治理能力

Features:
- `F-P2-03-01` 权限与项目空间
- `F-P2-03-02` 任务配额与资源治理
- `F-P2-03-03` 审计与可观测性看板

核心 AC:
1. 数据与任务访问具备最小权限控制。
2. 关键行为具备完整审计链路。

## 5. 非功能需求（NFR）

| NFR ID | 类别 | 需求定义 |
|---|---|---|
| `NFR-001` | 可靠性 | 核心任务状态与产物不可丢失，重启可恢复 |
| `NFR-002` | 可追溯性 | 关键决策 100% 可追溯到输入、证据、版本 |
| `NFR-003` | 可复现性 | 同输入+同随机种子应复现实验结果 |
| `NFR-004` | 安全性 | 审批、override、访问行为可审计 |
| `NFR-005` | 可观测性 | 所有 agent 节点具备耗时、状态、错误码 |
| `NFR-006` | 可降级性 | 子智能体失败时可降级到固定流程或人工接管 |

## 6. 统一验收包结构（研发与测试共同遵循）

每个 Feature 必须提交以下验收包：

1. 需求实现说明：变更点 + 约束 + 风险
2. 测试证据：
   - 单元测试结果
   - 集成测试结果
   - E2E 场景日志
3. 追踪更新：
   - 更新 `ACCEPTANCE_TRACE_MATRIX.md`
   - 更新文档中的 Feature 状态
4. 演示证据：
   - API 调用记录
   - 关键产物截图或结构化输出

## 7. Feature 状态字典（管理字段）

| 状态 | 含义 |
|---|---|
| `draft` | 已定义，未进入开发 |
| `ready` | 验收标准明确，可开发 |
| `in_dev` | 开发中 |
| `in_test` | 测试中 |
| `accepted` | 验收通过 |
| `blocked` | 受依赖/风险阻断 |

