# AI-Only Chat Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `gsagent chat` behave as an AI-first awakened assistant: every user turn is routed through the configured LLM, with no keyword intent gate and no local fallback response.

**Architecture:** The CLI loads runtime settings, requires a configured OpenAI-compatible LLM, and sends each chat turn to a strict JSON router prompt. The router decides `chat`, `gs_task`, or `exit`; only `gs_task` proceeds to GS job creation, and task fields come from explicit CLI overrides or the LLM router output.

**Tech Stack:** Python CLI, `OpenAICompatibleLLMClient`, Pydantic settings, pytest, existing GS job/report services.

---

## File Structure

- Modify: `src/animal_gs_agent/cli.py`
  - Remove keyword-based chat routing from `cmd_chat`.
  - Remove unused local regex task-field extraction from the CLI module.
  - Add an LLM router helper that returns normalized intent, reply, and GS task fields.
  - Require LLM configuration before any chat input is classified.
- Modify: `tests/unit/test_cli.py`
  - Replace keyword-gate tests with AI-routing tests.
  - Verify chat messages do not create jobs.
  - Verify GS task routing uses fields returned by AI.
  - Verify missing LLM settings stop chat before any local fallback.
- Modify: `docs/delivery/CAPABILITY_GAP_AND_UPGRADE_PLAN.md`
  - Record strict AI-only CLI interaction as a P0 interaction requirement.
- Modify: `docs/changelog/DEVELOPMENT_LOG.md`
  - Record the behavior change and verification commands.

## Task 1: Lock AI-Only Chat Behavior With Tests

**Files:**
- Modify: `tests/unit/test_cli.py`

- [ ] **Step 1: Remove keyword-router imports**

Remove `_is_analysis_intent` from the import list. The chat path must not expose a keyword gate in tests.

- [ ] **Step 2: Add small-talk AI routing test**

Add a test that monkeypatches `OpenAICompatibleLLMClient.request_json` to return:

```python
{"intent": "chat", "reply": "我是 GS Agent，当前通过已配置的大模型接口进行自然语言理解。"}
```

Expected assertions:

```python
assert exit_code == 0
assert calls["create_job"] == 0
assert "我是 GS Agent" in output
assert "trait_name / 性状" not in output
```

- [ ] **Step 3: Add GS task AI routing test**

Add a test that monkeypatches router output to:

```python
{
    "intent": "gs_task",
    "reply": "",
    "trait_name": "daily_gain",
    "phenotype_path": str(pheno),
    "genotype_path": str(geno),
}
```

Expected assertions:

```python
assert exit_code == 0
assert "job_id=job-chat" in output
assert "A1001" in output
```

- [ ] **Step 4: Add missing-AI hard-stop test**

Clear the three LLM env vars and call `cmd_chat` with a casual message.

Expected assertions:

```python
assert exit_code == 2
assert "AI 未接入" in output
assert calls["create_job"] == 0
```

- [ ] **Step 5: Run focused tests and confirm RED**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_cli.py -q
```

Expected before implementation: tests fail because `cmd_chat` still uses `_is_analysis_intent` and `_small_talk_reply`.

## Task 2: Implement Strict LLM Router

**Files:**
- Modify: `src/animal_gs_agent/cli.py`

- [ ] **Step 1: Add LLM settings guard**

Add:

```python
def _has_llm_settings(settings: LLMSettings) -> bool:
    return bool(settings.base_url and settings.api_key and settings.model)
```

- [ ] **Step 2: Add router helper**

Add:

```python
def _route_chat_message(message: str, llm_client: OpenAICompatibleLLMClient) -> dict[str, str]:
    system_prompt = (
        "你是 GS Agent 的对话路由器。必须返回严格 JSON。"
        "intent 只能是 chat、gs_task、exit。"
        "chat 表示普通对话或能力咨询，必须给 reply。"
        "gs_task 表示用户要启动基因组选择分析，尽量提取 trait_name、phenotype_path、genotype_path。"
        "exit 表示用户明确要求退出。"
        "不要使用 Markdown。"
    )
    payload = llm_client.request_json(system_prompt=system_prompt, user_prompt=message)
    ...
```

Normalize missing string fields to `""`, validate `intent`, and raise `ValueError` if the router response is invalid.

- [ ] **Step 3: Replace `cmd_chat` routing loop**

New flow:

```python
settings = get_settings()
if not _has_llm_settings(settings.llm):
    print("[gsagent] AI 未接入：无法进行动态对话判断。")
    return 2
llm_client = OpenAICompatibleLLMClient(settings.llm)
...
route = _route_chat_message(message, llm_client)
if route["intent"] == "chat":
    print(f"[gsagent] {route['reply']}")
    ...
if route["intent"] == "exit":
    print("[gsagent] 已退出。")
    return 0
```

For `gs_task`, use only:

```python
trait_name = args.trait_name or route["trait_name"] or _prompt_text("trait_name / 性状")
phenotype_path = args.phenotype_path or route["phenotype_path"] or _prompt_text("phenotype_path / 表型文件")
genotype_path = args.genotype_path or route["genotype_path"] or _prompt_text("genotype_path / 基因型文件")
```

Do not call local keyword, small-talk, or regex extraction helpers from `cmd_chat`.

- [ ] **Step 4: Remove unused local fallback helpers**

Delete `_is_analysis_intent`, `_small_talk_reply`, `_extract_value`, and `_extract_task_fields` from `cli.py`.

- [ ] **Step 5: Run focused tests and confirm GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_cli.py -q
```

Expected: all `test_cli.py` tests pass.

## Task 3: Update Delivery Documentation

**Files:**
- Modify: `docs/delivery/CAPABILITY_GAP_AND_UPGRADE_PLAN.md`
- Modify: `docs/changelog/DEVELOPMENT_LOG.md`

- [ ] **Step 1: Add capability note**

Under P0 capabilities, add that CLI awakened chat is strict AI-routed, not keyword-routed.

- [ ] **Step 2: Add changelog entry**

Record:

```markdown
## 2026-05-23

- Changed `gsagent chat` to strict AI-only turn routing.
- Removed keyword intent fallback and local small-talk fallback from the chat command.
- Added tests for AI chat routing, AI GS task routing, and missing-AI hard stop.
```

## Task 4: Verification, Commit, Push

**Files:**
- Verify all touched files.

- [ ] **Step 1: Run security scan**

Run:

Run the repository secret scan used by the maintainer. The scan pattern must cover OpenAI-style keys, GitHub PATs, and legacy `ghp_` tokens, but the exact regular expression should not be copied into this document because it would create a false-positive match in committed docs.

Expected: no committed secret in touched files.

- [ ] **Step 2: Run unit verification**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_cli.py tests/unit/services/test_html_report_service.py -q
.venv/bin/python -m compileall -q src/animal_gs_agent/cli.py
```

Expected: exit code 0 for both commands.

- [ ] **Step 3: Commit**

Run:

```bash
git add src/animal_gs_agent/cli.py tests/unit/test_cli.py docs/superpowers/plans/2026-05-23-ai-only-chat-routing.md docs/delivery/CAPABILITY_GAP_AND_UPGRADE_PLAN.md docs/changelog/DEVELOPMENT_LOG.md
git commit -m "fix(cli): require AI-routed chat turns"
```

- [ ] **Step 4: Push**

Run:

```bash
git push origin main
```

## Self-Review

- Spec coverage: covers strict AI-only routing, no keyword fallback, no local small-talk fallback, AI field extraction, docs, verification, commit, push.
- Placeholder scan: no TBD/TODO placeholders.
- Type consistency: helper names and fields match existing `LLMSettings`, `OpenAICompatibleLLMClient`, and CLI argument names.
