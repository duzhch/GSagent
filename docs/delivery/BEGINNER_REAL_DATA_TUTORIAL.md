# GS Agent 小白真实数据运行教程

本教程面向第一次使用 `GSagent` 的科研人员或测试人员，目标是把真实表型/基因型数据放到正确目录，并完成一次可复现的 GS 分析。

## 0. 先看结论

当前 GitHub 仓库可以作为智能体服务与 CLI 使用，但**真实 GS workflow 还依赖一个固定 Nextflow pipeline 目录**。

也就是说，新机器上要跑真实数据，必须同时准备：

1. `GSagent` 代码仓库。
2. Python/R/Nextflow/PLINK2 运行环境。
3. 可用的大模型 API 配置。
4. 固定 GS pipeline，目录内必须有 `main.nf`。
5. 真实数据文件，且路径必须在 `ANIMAL_GS_AGENT_ALLOWED_DATA_ROOTS` 白名单内。

如果缺少第 4 项，提交任务时会失败，典型错误是：

```text
workflow_pipeline_missing main.nf not found in <pipeline_dir>
```

## 1. 推荐目录结构

建议不要把数据直接放进代码仓库。推荐结构如下：

```text
/work/home/<user>/gsagent_project/
  GSagent/                  # GitHub clone 下来的代码仓库
  workdir/                  # 运行工作目录，放 .env、runs、state、pipeline
    .env
    pipeline/               # 固定 GS Nextflow pipeline，里面必须有 main.nf
    runs/                   # 每次任务输出
    state/                  # SQLite/状态文件，可选
  data/                     # 真实数据目录
    pig5/
      BF_phenotype.csv
      2548bir.bed
      2548bir.bim
      2548bir.fam
```

在本服务器当前项目中，对应路径是：

```text
代码仓库: /work/home/zyqlab/dzhichao/Agent0428/animal_gs_agent
工作目录: /work/home/zyqlab/dzhichao/Agent0428/animal_gs_agent
真实数据: /work/home/zyqlab/dzhichao/Agent0428/data
pipeline: /work/home/zyqlab/dzhichao/Agent0428/gs_prototype/pipeline
输出目录: /work/home/zyqlab/dzhichao/Agent0428/animal_gs_agent/runs
```

## 2. 数据格式要求

## 2.1 表型文件 phenotype CSV

表型文件必须是 CSV/TSV/TXT 表格，推荐 CSV。至少包含：

- `animal_id`：个体 ID
- 目标性状列：例如 `BF`

示例：

```csv
animal_id,BF
FS0013,9.64
FS0019,10.26
FS0027,10.94
```

注意：`trait_name` 必须和表型列名完全一致。例如提交 `trait_name=BF`，CSV 里必须有 `BF` 这一列。

## 2.2 基因型文件 genotype

当前真实 workflow 支持两类输入：

1. VCF：直接传 `.vcf`
2. PLINK BED 三件套：传 `.bed`，同目录必须同时存在 `.bim` 和 `.fam`

BED 示例：

```text
2548bir.bed
2548bir.bim
2548bir.fam
```

提交时 `genotype_path` 写 `.bed` 文件路径即可：

```text
/work/home/.../data/pig5/2548bir.bed
```

系统会检查同名前缀下是否存在 `.bim` 和 `.fam`。

## 3. 安装

进入代码仓库：

```bash
cd /work/home/<user>/gsagent_project/GSagent
```

推荐一键安装：

```bash
bash scripts/install_easy_gsagent.sh
```

如果提示找不到 `gsagent`：

```bash
export PATH="$HOME/.local/bin:$PATH"
```

检查命令是否存在：

```bash
gsagent --version
```

## 4. 准备工作目录和数据目录

以新项目为例：

```bash
mkdir -p /work/home/<user>/gsagent_project/workdir
mkdir -p /work/home/<user>/gsagent_project/workdir/runs
mkdir -p /work/home/<user>/gsagent_project/workdir/state
mkdir -p /work/home/<user>/gsagent_project/data/pig5
```

把真实数据放到：

```text
/work/home/<user>/gsagent_project/data/pig5/
```

例如：

```text
/work/home/<user>/gsagent_project/data/pig5/BF_phenotype.csv
/work/home/<user>/gsagent_project/data/pig5/2548bir.bed
/work/home/<user>/gsagent_project/data/pig5/2548bir.bim
/work/home/<user>/gsagent_project/data/pig5/2548bir.fam
```

## 5. 准备 pipeline

真实分析必须有固定 GS pipeline。pipeline 目录内必须有：

```text
main.nf
nextflow.config
modules/
bin/
```

推荐放到：

```text
/work/home/<user>/gsagent_project/workdir/pipeline
```

如果 pipeline 在其他地方，也可以不复制，但 `.env` 里必须把 `ANIMAL_GS_AGENT_WORKFLOW_PIPELINE_DIR` 指到正确目录。

本服务器当前可用 pipeline 示例：

```text
/work/home/zyqlab/dzhichao/Agent0428/gs_prototype/pipeline
```

## 6. 配置 .env

运行交互式配置：

```bash
gsagent configure --workdir /work/home/<user>/gsagent_project/workdir
```

如果你不想交互，也可以直接创建：

```bash
cat > /work/home/<user>/gsagent_project/workdir/.env <<'ENV'
ANIMAL_GS_AGENT_LLM_BASE_URL=https://api.deepseek.com
ANIMAL_GS_AGENT_LLM_API_KEY=replace-with-your-key
ANIMAL_GS_AGENT_LLM_MODEL=deepseek-chat
ANIMAL_GS_AGENT_LLM_TIMEOUT_SECONDS=30

ANIMAL_GS_AGENT_API_TOKEN=replace-with-a-long-random-token

ANIMAL_GS_AGENT_WORKFLOW_PIPELINE_DIR=/work/home/<user>/gsagent_project/workdir/pipeline
ANIMAL_GS_AGENT_WORKFLOW_OUTPUT_ROOT=/work/home/<user>/gsagent_project/workdir/runs
ANIMAL_GS_AGENT_WORKFLOW_EXECUTION_POLICY=auto

ANIMAL_GS_AGENT_ALLOWED_DATA_ROOTS=/work/home/<user>/gsagent_project/data

# 如果使用 Slurm，并希望 auto/slurm 提交，需要配置 submit 脚本
ANIMAL_GS_AGENT_SLURM_SUBMIT_SCRIPT=/work/home/<user>/gsagent_project/workdir/slurm_submit.sh
ANIMAL_GS_AGENT_AUTO_PREFER_SLURM=1
ENV
```

重要字段解释：

| 变量 | 含义 | 常见问题 |
|---|---|---|
| `ANIMAL_GS_AGENT_LLM_BASE_URL` | 大模型 API 地址 | 不配则 chat/API 不能做 AI 解析 |
| `ANIMAL_GS_AGENT_LLM_API_KEY` | 大模型 key | 不要提交到 GitHub |
| `ANIMAL_GS_AGENT_API_TOKEN` | 访问服务 API 的 token | 调 `/jobs` 必须带 |
| `ANIMAL_GS_AGENT_WORKFLOW_PIPELINE_DIR` | Nextflow pipeline 目录 | 必须包含 `main.nf` |
| `ANIMAL_GS_AGENT_WORKFLOW_OUTPUT_ROOT` | 分析输出目录 | 每个 job 一个子目录 |
| `ANIMAL_GS_AGENT_ALLOWED_DATA_ROOTS` | 允许读取的数据根目录 | 数据不在这里会 403 |
| `ANIMAL_GS_AGENT_WORKFLOW_EXECUTION_POLICY` | `auto/local/slurm` | 登录节点建议 `auto` 或 `slurm` |

## 7. 安装与配置检查

```bash
gsagent preflight --workdir /work/home/<user>/gsagent_project/workdir
```

预期：

```text
[gsagent] preflight OK
```

检查大模型：

```bash
gsagent llm-check --workdir /work/home/<user>/gsagent_project/workdir --message "health check"
```

预期：

```text
[gsagent] llm-check passed
```

## 8. 真实数据 contract check

在代码仓库目录执行：

```bash
cd /work/home/<user>/gsagent_project/GSagent
```

如果你用一键安装创建了 `gsagent_runtime` 环境：

```bash
conda run -n gsagent_runtime python scripts/native/real_data_contract_check.py \
  --trait BF \
  --phenotype-path /work/home/<user>/gsagent_project/data/pig5/BF_phenotype.csv \
  --genotype-path /work/home/<user>/gsagent_project/data/pig5/2548bir.bed
```

如果你在仓库自带 `.venv` 里运行：

```bash
.venv/bin/python scripts/native/real_data_contract_check.py \
  --trait BF \
  --phenotype-path /work/home/<user>/gsagent_project/data/pig5/BF_phenotype.csv \
  --genotype-path /work/home/<user>/gsagent_project/data/pig5/2548bir.bed
```

通过时应看到：

```json
"phenotype_exists": true,
"genotype_exists": true,
"trait_column_present": true,
"validation_flags": []
```

如果 `validation_flags` 不为空，先不要跑真实任务，按错误修数据。

## 9. 启动服务

终端 1：

```bash
gsagent serve \
  --workdir /work/home/<user>/gsagent_project/workdir \
  --host 0.0.0.0 \
  --port 8000 \
  --llm-check auto
```

保持这个终端不要关。

终端 2：

```bash
cd /work/home/<user>/gsagent_project/workdir
export GS_TOKEN=$(awk -F= '/^ANIMAL_GS_AGENT_API_TOKEN=/{print $2}' .env)
```

健康检查：

```bash
curl -s http://127.0.0.1:8000/health
```

受保护接口检查：

```bash
curl -s -H "X-API-Key: ${GS_TOKEN}" http://127.0.0.1:8000/worker/health
```

## 10. 提交真实 GS 任务

## 10.1 创建 job

```bash
SUBMIT_RESP=$(curl -s -X POST "http://127.0.0.1:8000/jobs" \
  -H "X-API-Key: ${GS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "user_message": "请对猪群体 BF 性状做基因组选择，输出候选个体排序。",
    "trait_name": "BF",
    "phenotype_path": "/work/home/<user>/gsagent_project/data/pig5/BF_phenotype.csv",
    "genotype_path": "/work/home/<user>/gsagent_project/data/pig5/2548bir.bed"
  }')

echo "$SUBMIT_RESP" | python3 -m json.tool
export JOB_ID=$(echo "$SUBMIT_RESP" | python3 -c 'import json,sys; print(json.load(sys.stdin)["job_id"])')
echo "JOB_ID=$JOB_ID"
```

如果返回 403：检查 `ANIMAL_GS_AGENT_ALLOWED_DATA_ROOTS`。

如果返回 503：检查 LLM 配置。

## 10.2 运行 job

```bash
curl -s -X POST "http://127.0.0.1:8000/jobs/${JOB_ID}/run" \
  -H "X-API-Key: ${GS_TOKEN}" | python3 -m json.tool
```

如果配置是 `local`，API 会等待 workflow 执行完成。

如果配置是 `auto/slurm` 且当前是登录节点，可能返回 `submitted`，表示已提交到 Slurm。

## 10.3 查看状态

```bash
curl -s -H "X-API-Key: ${GS_TOKEN}" \
  "http://127.0.0.1:8000/jobs/${JOB_ID}" | python3 -m json.tool
```

重点看：

```text
status
execution_error
execution_error_detail
workflow_submission_id
workflow_result_dir
```

## 10.4 查看报告

```bash
curl -s -H "X-API-Key: ${GS_TOKEN}" \
  "http://127.0.0.1:8000/jobs/${JOB_ID}/report" | python3 -m json.tool
```

## 10.5 查看输出工件

```bash
curl -s -H "X-API-Key: ${GS_TOKEN}" \
  "http://127.0.0.1:8000/jobs/${JOB_ID}/artifacts" | python3 -m json.tool
```

输出文件通常位于：

```text
/work/home/<user>/gsagent_project/workdir/runs/<JOB_ID>/
```

常见结果包括：

```text
gebv_rankings.csv
breeding_report.md
reports/gs_report.html
```

具体以 `/artifacts` 返回为准。

## 11. 用 chat 入口运行或辅助检查

启动：

```bash
gsagent chat --workdir /work/home/<user>/gsagent_project/workdir
```

可以先问：

```text
看下我当前目录下有什么文件
```

如果要启动 GS 任务，可以说：

```text
请对 BF 做基因组选择，表型文件是 /work/home/<user>/gsagent_project/data/pig5/BF_phenotype.csv，基因型文件是 /work/home/<user>/gsagent_project/data/pig5/2548bir.bed，输出候选个体。
```

注意：chat 入口适合交互式演示和小规模测试；正式批量运行建议用 API，因为 API 更容易记录 job id、状态、报告和工件。

## 12. Slurm 集群运行建议

登录节点不要强行跑本地重计算。建议：

```env
ANIMAL_GS_AGENT_WORKFLOW_EXECUTION_POLICY=auto
ANIMAL_GS_AGENT_AUTO_PREFER_SLURM=1
ANIMAL_GS_AGENT_SLURM_SUBMIT_SCRIPT=/path/to/slurm_submit.sh
```

如果一定要在当前节点本地跑：

```env
ANIMAL_GS_AGENT_WORKFLOW_EXECUTION_POLICY=local
```

但这只适合小数据或计算节点，不建议在登录节点使用。

## 13. 常见错误排查

| 现象 | 原因 | 解决 |
|---|---|---|
| `gsagent: command not found` | `~/.local/bin` 不在 PATH | `export PATH="$HOME/.local/bin:$PATH"` |
| `AI 未接入` 或 503 | LLM 配置缺失 | 检查 `.env` 的 LLM 三项 |
| `data_path_outside_allowed_roots` | 数据不在白名单 | 把数据目录加入 `ANIMAL_GS_AGENT_ALLOWED_DATA_ROOTS` |
| `trait_column_missing` | 表型文件没有目标列 | 确认 `trait_name` 与 CSV 列名一致 |
| `bed input is incomplete` | 缺少 `.bim` 或 `.fam` | 确保 BED 三件套同前缀同目录 |
| `workflow_pipeline_missing` | pipeline 目录错或缺 `main.nf` | 修正 `ANIMAL_GS_AGENT_WORKFLOW_PIPELINE_DIR` |
| `workflow_dependency_missing` | 缺 `plink2`/`nextflow`/`Rscript` | 重新安装 runtime 或检查 conda env |
| Slurm 提交失败 | submit 脚本未配置或无权限 | 检查 `ANIMAL_GS_AGENT_SLURM_SUBMIT_SCRIPT` |

## 14. 当前服务器已验证情况

截至 2026-05-26，本服务器当前代码版本与 GitHub `origin/main` 一致：

```text
8905145 feat(cli): add AI-routed directory listing
```

已验证：

1. `gsagent preflight --workdir /work/home/zyqlab/dzhichao/Agent0428/animal_gs_agent` 通过。
2. 真实数据 contract check 通过：
   - trait: `BF`
   - phenotype: `/work/home/zyqlab/dzhichao/Agent0428/data/pig5/BF_phenotype.csv`
   - genotype: `/work/home/zyqlab/dzhichao/Agent0428/data/pig5/2548bir.bed`
3. contract check 结果：
   - `phenotype_exists=true`
   - `genotype_exists=true`
   - `trait_column_present=true`
   - `validation_flags=[]`

未在本次检查中直接启动完整 Nextflow 真实计算；完整运行仍需占用计算资源，建议在 Slurm/计算节点或明确允许的环境中执行。
