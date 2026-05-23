from pathlib import Path
import io
import os
from types import SimpleNamespace

import pytest

from animal_gs_agent.cli import (
    _prepare_runtime,
    _prompt_text,
    _required_command_missing,
    _resolve_workdir,
    build_parser,
    cmd_chat,
    cmd_configure,
)


def test_resolve_workdir_rejects_missing_path(tmp_path: Path) -> None:
    missing = tmp_path / "not_exists"
    with pytest.raises(FileNotFoundError):
        _resolve_workdir(str(missing))


def test_prepare_runtime_loads_env_file_without_overriding_existing(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "ANIMAL_GS_AGENT_LLM_BASE_URL=https://example.com",
                "ANIMAL_GS_AGENT_LLM_MODEL=demo-model",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_MODEL", "preset-model")

    original_cwd = Path.cwd()
    try:
        resolved = _prepare_runtime(workdir=str(tmp_path), env_file=".env")
        assert resolved == tmp_path.resolve()
        assert Path.cwd() == tmp_path.resolve()
        assert os.environ["ANIMAL_GS_AGENT_WORKDIR"] == str(tmp_path.resolve())
        assert os.environ["ANIMAL_GS_AGENT_LLM_BASE_URL"] == "https://example.com"
        # existing env should not be overridden by .env loader
        assert os.environ["ANIMAL_GS_AGENT_LLM_MODEL"] == "preset-model"
    finally:
        os.chdir(original_cwd)


def test_parser_contains_expected_subcommands() -> None:
    parser = build_parser()
    action = next(item for item in parser._actions if item.dest == "command")
    subcommands = set(action.choices.keys())
    assert {"preflight", "serve", "worker", "print-env", "llm-check", "configure", "init", "chat", "run"}.issubset(
        subcommands
    )


def test_required_command_missing_accepts_python3_fallback(monkeypatch) -> None:
    available = {"python3", "nextflow", "plink2", "Rscript"}

    monkeypatch.setattr(
        "animal_gs_agent.cli.shutil.which",
        lambda cmd: f"/usr/bin/{cmd}" if cmd in available else None,
    )

    assert _required_command_missing() == []


def test_prompt_text_accepts_gb18030_chinese_when_terminal_claims_utf8(monkeypatch) -> None:
    raw_stdin = io.BytesIO("你是谁\n".encode("gb18030"))
    monkeypatch.setattr("sys.stdin", io.TextIOWrapper(raw_stdin, encoding="utf-8"))

    assert _prompt_text("你") == "你是谁"


def test_prompt_text_applies_ctrl_h_backspace(monkeypatch) -> None:
    raw_stdin = io.BytesIO("你是x\b谁\n".encode("utf-8"))
    monkeypatch.setattr("sys.stdin", io.TextIOWrapper(raw_stdin, encoding="utf-8"))

    assert _prompt_text("你") == "你是谁"


def test_prompt_text_applies_delete_backspace(monkeypatch) -> None:
    raw_stdin = io.BytesIO("你是x\x7f谁\n".encode("utf-8"))
    monkeypatch.setattr("sys.stdin", io.TextIOWrapper(raw_stdin, encoding="utf-8"))

    assert _prompt_text("你") == "你是谁"


def test_configure_creates_env_with_interactive_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_inputs = iter(
        [
            "https://api.deepseek.com",
            "deepseek-chat",
            "token-demo",
            "auto",
            str(tmp_path / "pipeline"),
            str(tmp_path / "runs"),
            str(tmp_path / "submit.sh"),
            f"{tmp_path}/data,{tmp_path}/shared",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
    monkeypatch.setattr("animal_gs_agent.cli.getpass", lambda _: "test-secret-123")
    monkeypatch.setattr("animal_gs_agent.cli.secrets.token_urlsafe", lambda _: "token-demo")

    args = SimpleNamespace(workdir=str(tmp_path), env_file=".env")
    exit_code = cmd_configure(args)

    assert exit_code == 0
    env_content = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "ANIMAL_GS_AGENT_LLM_BASE_URL=https://api.deepseek.com" in env_content
    assert "ANIMAL_GS_AGENT_LLM_API_KEY=test-secret-123" in env_content
    assert "ANIMAL_GS_AGENT_LLM_MODEL=deepseek-chat" in env_content
    assert "ANIMAL_GS_AGENT_API_TOKEN=token-demo" in env_content
    assert f"ANIMAL_GS_AGENT_WORKFLOW_PIPELINE_DIR={tmp_path / 'pipeline'}" in env_content
    assert f"ANIMAL_GS_AGENT_WORKFLOW_OUTPUT_ROOT={tmp_path / 'runs'}" in env_content
    assert f"ANIMAL_GS_AGENT_SLURM_SUBMIT_SCRIPT={tmp_path / 'submit.sh'}" in env_content
    assert f"ANIMAL_GS_AGENT_ALLOWED_DATA_ROOTS={tmp_path}/data,{tmp_path}/shared" in env_content


def test_configure_keeps_existing_secret_when_blank_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "ANIMAL_GS_AGENT_LLM_BASE_URL=https://api.deepseek.com",
                "ANIMAL_GS_AGENT_LLM_API_KEY=existing-key",
                "ANIMAL_GS_AGENT_LLM_MODEL=deepseek-chat",
                "ANIMAL_GS_AGENT_API_TOKEN=existing-token",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    user_inputs = iter(["", "", "", "", "", "", "", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
    monkeypatch.setattr("animal_gs_agent.cli.getpass", lambda _: "")

    args = SimpleNamespace(workdir=str(tmp_path), env_file=".env")
    exit_code = cmd_configure(args)

    assert exit_code == 0
    loaded = env_file.read_text(encoding="utf-8")
    assert "ANIMAL_GS_AGENT_LLM_API_KEY=existing-key" in loaded
    assert "ANIMAL_GS_AGENT_API_TOKEN=existing-token" in loaded


def test_chat_uses_ai_for_small_talk_without_running_job(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    calls = {"create_job": 0}
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_API_KEY", "secret-key")
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_MODEL", "deepseek-chat")
    monkeypatch.setattr(
        "animal_gs_agent.cli.OpenAICompatibleLLMClient.request_json",
        lambda self, system_prompt, user_prompt: {
            "intent": "chat",
            "reply": "我是 GS Agent，当前通过已配置的大模型接口进行自然语言理解。",
        },
    )
    monkeypatch.setattr(
        "animal_gs_agent.cli.create_job",
        lambda *args, **kwargs: calls.__setitem__("create_job", calls["create_job"] + 1),
    )

    args = SimpleNamespace(
        workdir=str(tmp_path),
        env_file=".env",
        message="你好",
        trait_name=None,
        phenotype_path=None,
        genotype_path=None,
    )

    exit_code = cmd_chat(args)

    assert exit_code == 0
    assert calls["create_job"] == 0
    output = capsys.readouterr().out
    assert "我是 GS Agent" in output
    assert "trait_name / 性状" not in output


def test_interactive_chat_routes_exit_through_ai_after_small_talk(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    calls = {"create_job": 0, "request_json": 0}
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_API_KEY", "secret-key")
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_MODEL", "deepseek-chat")
    user_inputs = iter(["你好啊，你是什么模型", "退出"])
    monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))

    def fake_request_json(self, system_prompt, user_prompt):
        calls["request_json"] += 1
        if calls["request_json"] == 1:
            assert user_prompt == "你好啊，你是什么模型"
            return {
                "intent": "chat",
                "reply": "我是 GS Agent，当前通过已配置的大模型接口进行自然语言理解。",
            }
        assert user_prompt == "退出"
        return {"intent": "exit", "reply": "", "trait_name": "", "phenotype_path": "", "genotype_path": ""}

    monkeypatch.setattr("animal_gs_agent.cli.OpenAICompatibleLLMClient.request_json", fake_request_json)
    monkeypatch.setattr(
        "animal_gs_agent.cli.create_job",
        lambda *args, **kwargs: calls.__setitem__("create_job", calls["create_job"] + 1),
    )

    args = SimpleNamespace(
        workdir=str(tmp_path),
        env_file=".env",
        message=None,
        trait_name=None,
        phenotype_path=None,
        genotype_path=None,
    )

    exit_code = cmd_chat(args)

    assert exit_code == 0
    assert calls["request_json"] == 2
    assert calls["create_job"] == 0
    output = capsys.readouterr().out
    assert "我是 GS Agent" in output
    assert "已退出" in output


def test_chat_requires_ai_for_dynamic_routing(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    calls = {"create_job": 0}
    monkeypatch.delenv("ANIMAL_GS_AGENT_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("ANIMAL_GS_AGENT_LLM_API_KEY", raising=False)
    monkeypatch.delenv("ANIMAL_GS_AGENT_LLM_MODEL", raising=False)
    monkeypatch.setattr(
        "animal_gs_agent.cli.create_job",
        lambda *args, **kwargs: calls.__setitem__("create_job", calls["create_job"] + 1),
    )

    args = SimpleNamespace(
        workdir=str(tmp_path),
        env_file=".env",
        message="你好啊，你是什么模型",
        trait_name=None,
        phenotype_path=None,
        genotype_path=None,
    )

    exit_code = cmd_chat(args)

    assert exit_code == 2
    assert calls["create_job"] == 0
    output = capsys.readouterr().out
    assert "AI 未接入" in output
    assert "trait_name / 性状" not in output


def test_chat_command_runs_job_from_single_message(tmp_path: Path, monkeypatch, capsys) -> None:
    pheno = tmp_path / "pheno.csv"
    geno = tmp_path / "geno.vcf"
    pheno.write_text("animal_id,daily_gain\nA1,1.0\n", encoding="utf-8")
    geno.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_API_KEY", "secret-key")
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_MODEL", "deepseek-chat")
    monkeypatch.setattr(
        "animal_gs_agent.cli.OpenAICompatibleLLMClient.request_json",
        lambda self, system_prompt, user_prompt: {
            "intent": "gs_task",
            "reply": "",
            "trait_name": "daily_gain",
            "phenotype_path": str(pheno),
            "genotype_path": str(geno),
        },
    )

    class FakeTask:
        candidate_fixed_effects = []

    class FakeProfile:
        risk_tags = []

    class FakeJob:
        job_id = "job-chat"
        status = "queued"
        trait_name = "daily_gain"
        workflow_result_dir = None

    class FakeCompleted:
        job_id = "job-chat"
        status = "completed"
        trait_name = "daily_gain"
        workflow_result_dir = str(tmp_path / "runs" / "job-chat")

    class FakeCandidate:
        individual_id = "A1001"
        gebv = 1.23
        rank = 1

    class FakeArtifact:
        artifact_path = str(tmp_path / "runs" / "job-chat" / "reports" / "gs_report.html")

    class FakeReport:
        report_text = "AI 生成：A1001 是优先候选。"
        top_candidates = [FakeCandidate()]
        html_report_artifact = FakeArtifact()

    monkeypatch.setattr("animal_gs_agent.cli.understand_task", lambda message, llm_client: FakeTask())
    monkeypatch.setattr("animal_gs_agent.cli.build_dataset_profile", lambda payload: FakeProfile())
    monkeypatch.setattr(
        "animal_gs_agent.cli.create_job",
        lambda payload, task_understanding, dataset_profile: FakeJob(),
    )
    monkeypatch.setattr("animal_gs_agent.cli.run_job", lambda *args, **kwargs: FakeCompleted())
    monkeypatch.setattr("animal_gs_agent.cli.build_job_report", lambda job: FakeReport())

    args = SimpleNamespace(
        workdir=str(tmp_path),
        env_file=".env",
        message=(
            f"请对 daily_gain 做GS phenotype_path={pheno} "
            f"genotype_path={geno} 输出候选个体"
        ),
        trait_name=None,
        phenotype_path=None,
        genotype_path=None,
    )

    exit_code = cmd_chat(args)

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "唤醒成功" in output
    assert "job_id=job-chat" in output
    assert "A1001" in output
    assert "gs_report.html" in output
