# PRD: High-Standard GS Agent Hardness (For Researchers & Breeding Practitioners)

## 1. 背景与目标

当前项目已经具备可运行的 GS MVP（任务提交、固定流程执行、报告与产物输出、离线打包），但核心价值仍偏向“可重复 workflow 服务”。  
本 PRD 的目标是将产品升级为**真实可用的垂直智能体（Hardness）**：

- 减少用户决策负担（让用户少做“如何做”的选择）
- 提高研发与生产效率（减少无效试验、缩短迭代路径）
- 提升结果置信度（可审计、可解释、可复现、可量化不确定性）
- 明确体现大模型作用（不止 NL 接口，而是高价值决策与反思能力）

## 2. 目标用户与使用场景

### 2.1 目标用户

- 科研人员：遗传评估/基因组选育研究者、研究生、计算生物团队
- 产业从业者：育种公司算法团队、数据平台主管、场内遗传评估人员

### 2.2 典型任务

- 群体内预测：群体 A 的性状 T 的 GEBV 预测与排序
- 跨群体验证：A 训练、B 测试，评估泛化
- 预算约束下模型选择：在有限 trial 数下接近最优性能
- 生产审计：报告是否可信、是否存在数据偏差/流程偏差

## 3. 产品定位与边界

### 3.1 产品定位

“工作流引擎 + 多智能体决策层 + 审计层 + 记忆层”的科研与育种决策系统。

### 3.2 非目标（明确不做）

- 通用生信聊天机器人
- 任意 shell 自动执行器（无边界工具调用）
- 仅靠提示词做“看似智能”的黑盒系统

## 4. 当前实现审计（基于仓库现状）

## 4.1 已具备能力

- 任务提交、状态机、异步队列、持久化恢复
- 固定 GS pipeline（Nextflow）执行与结果解析
- 基础数据契约检查（路径/格式/表头/trait）
- 结构化报告与产物清单输出
- Slurm 场景与离线打包交付

## 4.2 与理想态差距

- 缺少真正多智能体分工（总控/数据/模型/知识/审计/报告/debug）
- 缺少模型策略层（GBLUP/BayesB/XGBoost 的任务自适应选择）
- 缺少系统化 QC（群体结构、异常值、批次效应、系谱冲突等）
- 缺少置信度与不确定性量化（仅点估计，置信信息不足）
- 缺少知识更新与 badcase 记忆闭环
- 缺少研究级评测面板（Regret、Top-1 命中率、Trials-to-95%-Best）

结论：当前是**合格 MVP Harness**，但尚不是“高标准 Hardness 智能体”。

## 5. 产品原则（必须遵循）

1. 决策透明：每个关键决策必须给出依据与备选方案比较。
2. 风险前置：先做数据与设定风险扫描，再做模型执行。
3. 可复现优先：所有输出都可追溯到输入、参数、代码版本和环境。
4. 大模型用于高价值环节：任务拆解、策略搜索、证据整合、审计反思，而不是替代数值计算内核。
5. 人机协同：高风险节点必须支持人工确认。

## 6. 需求优先级（不设时间，仅排序）

## P0（最高优先级，决定“是否是智能体”）

### P0-1 多智能体总控编排（Supervisor Graph）

- 需求：建立显式总控智能体，调度数据、模型、审计、报告子智能体。
- 价值：把“流程执行”升级为“任务决策执行”。
- 验收：
  - 每次任务输出完整决策轨迹（agent 路径、输入输出、理由）
  - 支持失败重试与分支回退（非整任务重跑）

### P0-2 数据智能体（深度 QC 与风险画像）

- 需求：在现有格式检查基础上，新增 QC 模块：
  - 缺失率（样本/位点）
  - MAF 分布与过滤建议
  - 群体结构 PCA/聚类异常
  - 重复样本/近亲关系检测
  - 表型异常值检测
  - 批次效应诊断
  - 系谱冲突检测（当系谱可用时）
- 价值：减少垃圾输入导致的无效试验与错误结论。
- 验收：
  - 输出结构化 QC 报告（风险等级 + 建议动作）
  - 任一高风险项未处理前，默认阻断模型执行（可人工 override）

### P0-3 模型智能体（策略选择而非固定单模型）

- 需求：建立候选模型池与策略搜索：
  - GBLUP / BayesB / XGBoost（首批）
  - 支持协变量配置搜索
  - 支持预算约束（最大 trials）
  - 支持群体内、跨群体两种评估协议
- 价值：将“固定 pipeline”升级为“任务自适应决策”。
- 验收：
  - 输出：模型选择理由、被拒模型原因、预算消耗轨迹
  - 可回放：给定同一输入与随机种子，结果可复现

### P0-4 审计智能体（结果置信度与反证检查）

- 需求：新增独立审计层，审查：
  - 指标口径一致性（Pearson/RMSE）
  - 数据泄漏风险（训练/验证边界）
  - 过拟合与不稳定警告
  - 结论与证据一致性
- 价值：把“能跑完”升级为“可信可用”。
- 验收：
  - 每个结论必须有证据链接（文件、指标、日志）
  - 审计结论可标注为通过/警告/拒绝

### P0-5 评测指标体系产品化

- 需求：将你的论文指标固化到系统：
  - 预测性能：Pearson、RMSE
  - 决策质量：Top-1 命中率、Regret（相对 Oracle-best）
  - 搜索效率：Trials-to-95%-Best、无效试验率
- 价值：产品目标与科研目标统一。
- 验收：
  - 每次任务自动输出上述指标
  - 支持按群体/性状/模型维度聚合对比

## P1（高优先级，决定“是否可持续进化”）

### P1-1 知识智能体（RAG + 文献证据）

- 需求：接入可控知识库：
  - 历史育种记录
  - 内部 SOP 与约束
  - 外部文献与方法综述
- 价值：避免仅依赖当前任务上下文，提升决策稳定性。
- 验收：
  - 每个关键建议输出证据引用（文献/历史案例）
  - 支持证据冲突标注

### P1-2 Badcase 记忆闭环

- 需求：将失败任务、审计拒绝、用户纠正写入记忆库。
- 价值：持续降低重复错误，提高系统长期表现。
- 验收：
  - 新任务规划中可自动检索相似 badcase 并给规避建议
  - badcase 影响可量化（失败率下降趋势）

### P1-3 多角色报告

- 需求：输出三类报告：
  - 技术报告（参数、日志、指标、审计）
  - 决策报告（推荐方案、风险、备选）
  - 管理报告（效率、成本、收益）
- 价值：提高跨角色协作效率。
- 验收：
  - 同一任务可一键生成多视图报告
  - 报告结论一致，颗粒度不同

### P1-4 人机协同控制点

- 需求：在高风险节点设置人工审批（如高偏差数据仍强行运行）。
- 价值：在可靠性与自动化之间保持平衡。
- 验收：
  - 提供 override 记录与责任追踪
  - 审批行为纳入审计日志

## P2（中优先级，决定“规模化和论文竞争力”）

### P2-1 对比基线自动化实验台

- 需求：内建实验编排，自动跑：
  - 单智能体 / ReAct / 多智能体方法
  - 取消某子智能体的消融实验
  - 取消参考脚本或工具时的扰动实验
- 价值：直接服务论文结果图和方法有效性证明。
- 验收：
  - 一键生成对比表和图
  - 结果可复现实验记录

### P2-2 Debug 智能体

- 需求：自动定位失败原因、提出修复建议、控制重试次数、超限回退人工。
- 价值：减少“无限重试”和人为排错开销。
- 验收：
  - 失败任务自动分类（环境/数据/代码/资源）
  - 重试策略可配置且可审计

### P2-3 平台化能力

- 需求：权限体系、项目空间、任务配额、可观测性、成本看板。
- 价值：从“个人工具”升级为“团队基础设施”。
- 验收：
  - 任务与数据访问有清晰授权边界
  - 关键行为全链路可追溯

## 7. 大模型能力的“必须体现点”（产品约束）

以下能力必须由 LLM/Agent 层承担，且可被验证：

1. 任务抽象与实验计划生成  
从自然语言目标到结构化“任务定义 + 评估协议 + 预算策略”。

2. 策略搜索与动态决策  
在预算约束下自适应选择模型、协变量、验证策略，而非固定模板。

3. 证据整合与冲突处理  
整合历史记录、文献证据、当前数据诊断，输出可解释结论。

4. 审计反思与自我纠偏  
识别自身决策风险，输出置信级别和下一步建议。

不应由 LLM 直接替代的能力：

- 数值计算核心（矩阵运算、训练内核、统计估计）
- 硬约束校验（文件、格式、权限、安全策略）

## 8. 统一验收标准（Definition of Done for Hardness）

当且仅当以下条件满足，才可称为“高标准 GS 智能体”：

1. 至少 4 个子智能体协同稳定运行（总控、数据、模型、审计为最低集合）。
2. 在真实任务上相对固定基线显著减少无效试验率。
3. 在预算约束下实现更低 Regret 或更快达到 95% 最优性能。
4. 所有关键结论具备可追溯证据链。
5. 对 badcase 有记忆和规避效果（可量化）。

## 9. 风险与对策（按优先级）

1. 幻觉与错误决策风险  
对策：审计智能体 + 证据强约束 + 高风险人工审批。

2. 数据质量不稳定  
对策：数据智能体前置阻断 + 风险分级。

3. 指标与业务目标脱节  
对策：统一指标面板，任务目标与评估指标强绑定。

4. 系统复杂度上升  
对策：分层架构与可观测性先行，保持“可降级到固定流程”能力。

## 10. 外部调研摘要（用于产品决策依据）

- GS 领域核心共识：从 Meuwissen 等提出的 genome-wide marker prediction 出发，GS 的本质是用全基因组标记预测育种值；模型与训练群体设计显著影响准确性。
- 工具与流程共识：PLINK2 等工具在缺失率/MAF/PCA 等 QC 环节是事实标准；Nextflow 在可复现执行与断点恢复方面成熟。
- 智能体研究共识：在科研/数据分析任务上，当前前沿模型离“端到端全自动可靠科研”仍有明显差距，必须通过分工、评测、审计和可控工具环境提高可靠性。

## 11. 参考资料（调研来源）

1. Meuwissen TH, Hayes BJ, Goddard ME. Prediction of total genetic value using genome-wide dense marker maps (2001)  
   https://research.wur.nl/en/publications/prediction-of-total-genetic-value-using-genome-wide-dense-marker-/
2. VanRaden PM. Efficient Methods to Compute Genomic Predictions (JDS, 2008; USDA ARS record)  
   https://www.ars.usda.gov/research/publications/publication/?seqNo115=220301
3. Genomic selection in livestock populations (review)  
   https://www.cambridge.org/core/journals/genetics-research/article/genomic-selection-in-livestock-populations/AFC072298EB93F0637E8C9C1165D82B8
4. PLINK2 input filtering（`--geno/--mind/--maf`）  
   https://www.cog-genomics.org/plink/2.0/filter
5. PLINK2 population stratification / PCA / outlier related guidance  
   https://www.cog-genomics.org/plink/2.0/strat
6. Nextflow caching & resume（可复现执行关键机制）  
   https://docs.seqera.io/nextflow/cache-and-resume
7. Frontiers review: ML models in genomic prediction for animal breeding (2023)  
   https://www.frontiersin.org/journals/genetics/articles/10.3389/fgene.2023.1150596/full
8. ScienceAgentBench (2024): scientific discovery agents need rigorous task-level assessment  
   https://arxiv.org/abs/2410.05080
9. DABstep (OpenReview): 450+ multi-step data-analysis tasks, best agents still low accuracy on hardest set  
   https://openreview.net/pdf?id=E0xUHr3iP8
10. BixBench (2025): bioinformatics agent benchmark, frontier models表现仍受限  
    https://ar5iv.org/abs/2503.00096
11. Biomni (Stanford): general-purpose biomedical agent architecture (reasoning + retrieval + code execution)  
    https://biomni.stanford.edu/paper.pdf
12. LangGraph multi-agent coordination tutorial（监督者+专业子代理+共享状态）  
    https://langchain-ai-langgraph-40.mintlify.app/tutorials/multi-agent

