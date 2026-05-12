# Animal GS Agent（中文说明）

Animal GS Agent 是一个面向动物育种基因组选择（GS）的智能体系统。

- 能理解自然语言任务
- 能校验表型/基因型数据是否可用于分析
- 能触发固定流程的 GS 计算（Nextflow + PLINK2 + R）
- 能输出结果解释与工件信息

英文版本请见 `README.md`。

## 一、推荐安装方式（新手/测试团队）

在仓库根目录执行：

```bash
bash scripts/install_easy_gsagent.sh
```

该脚本会自动完成：

1. 没有 conda 时自动安装 Miniforge
2. 创建/更新运行环境（含 `plink2`、`nextflow`、`Rscript`）
3. 安装项目本体
4. 安装全局命令 `gsagent` 到 `~/.local/bin`

如果提示 `gsagent: command not found`，执行：

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## 二、交互式配置 API（最简步骤）

在你要运行的工作目录执行：

```bash
gsagent configure --workdir /path/to/project
```

或使用别名：

```bash
gsagent init --workdir /path/to/project
```

该命令会交互询问并写入 `/path/to/project/.env`：

- LLM Base URL
- LLM API Key（隐藏输入）
- LLM 模型名
- API 鉴权 Token
- workflow 执行策略与路径
- 数据路径白名单

说明：

- 如果 `.env` 已存在，会按键更新，不会整文件覆盖
- API Key 留空表示保留已有值

## 三、安装后验证

```bash
gsagent preflight --workdir /path/to/project
gsagent llm-check --workdir /path/to/project --message "health check"
```

预期：

- `preflight OK`
- `llm-check passed`

## 四、启动服务

```bash
gsagent serve --workdir /path/to/project --host 0.0.0.0 --port 8000 --llm-check auto
```

## 五、API 冒烟测试（可直接复制）

新开一个终端：

```bash
cd /path/to/project
export GS_TOKEN=$(awk -F= '/^ANIMAL_GS_AGENT_API_TOKEN=/{print $2}' .env)

# 健康检查（公开接口，预期 200）
curl -s http://127.0.0.1:8000/health

# 无 token 访问受保护接口（预期 401）
curl -s http://127.0.0.1:8000/worker/health

# 带 token 访问受保护接口（预期 200）
curl -s -H "X-API-Key: ${GS_TOKEN}" http://127.0.0.1:8000/worker/health
```

## 六、真实作业冒烟（BED 输入示例）

```bash
curl -s -X POST "http://127.0.0.1:8000/jobs" \
  -H "X-API-Key: ${GS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "user_message": "Run BF genomic selection with fixed effects sex and batch",
    "trait_name": "BF",
    "phenotype_path": "/path/to/data/BF_phenotype.csv",
    "genotype_path": "/path/to/data/2548bir.bed"
  }'
```

## 七、集群安全默认行为（Slurm）

- `ANIMAL_GS_AGENT_WORKFLOW_EXECUTION_POLICY=auto` 默认优先走 Slurm 提交，避免在登录节点重计算
- 当主机名包含 `login/head/front/submit/mgmt`，或检测到 `sbatch` 且当前不在 `SLURM_JOB_ID` 分配内时，会倾向提交
- `ANIMAL_GS_AGENT_WORKFLOW_PIPELINE_DIR` 与 `ANIMAL_GS_AGENT_WORKFLOW_OUTPUT_ROOT` 默认是 `<workdir>/pipeline` 和 `<workdir>/runs`

## 八、安全默认行为

- 业务接口默认需要 token：
  - `X-API-Key: <token>`
  - 或 `Authorization: Bearer <token>`
- `/health` 保持公开，便于探针与监控
- 提交作业的输入路径会受 `ANIMAL_GS_AGENT_ALLOWED_DATA_ROOTS` 约束

## 九、其他安装方式（高级用户）

仅安装 `gsagent` 启动器（不安装 `plink2/nextflow/Rscript`）：

```bash
bash scripts/install_global_gsagent.sh
```

可编辑安装：

```bash
python -m pip install -e .
```

手动安装完整运行环境：

```bash
conda env create -f packaging/native/environment.yml
conda activate gsagent_native
```

## 十、相关文档

- 运行时打包：`packaging/runtime/README.md`
- 离线打包：`packaging/release/README_OFFLINE.md`
- Singularity/Apptainer：`packaging/singularity/README.md`
