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
    cmd_autogs,
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
    assert {"preflight", "serve", "worker", "print-env", "llm-check", "configure", "init", "chat", "run", "autogs"}.issubset(
        subcommands
    )


def test_parser_exposes_autogs_screenshot_demo_subcommand() -> None:
    parser = build_parser()
    args = parser.parse_args(["autogs"])
    assert args.command == "autogs"


def test_parser_accepts_autogs_autonomous_run_message() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "autogs",
            "Perform Genomic Selection analysis on LargeWhite_Mini focusing on Backfat",
            "--trait-name",
            "Backfat",
            "--phenotype-path",
            "data/LargeWhite_Mini.pheno",
            "--genotype-path",
            "data/LargeWhite_Mini.vcf",
        ]
    )

    assert args.command == "autogs"
    assert args.message.startswith("Perform Genomic Selection")
    assert args.trait_name == "Backfat"
    assert args.phenotype_path == "data/LargeWhite_Mini.pheno"
    assert args.genotype_path == "data/LargeWhite_Mini.vcf"


def test_autogs_command_prints_gs_terminal_demo(tmp_path: Path, capsys) -> None:
    args = SimpleNamespace(
        workdir=str(tmp_path),
        env_file=".env",
        html_output=None,
        message=None,
        trait_name=None,
        phenotype_path=None,
        genotype_path=None,
    )

    exit_code = cmd_autogs(args)

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "AutoGS" in output
    assert "Breeding Intelligent Agent" in output
    assert "Genomic Selection" in output
    assert "LargeWhite_Mini" in output
    assert "Backfat" in output
    assert "GEBV" in output
    assert "GWAS" not in output


def test_autogs_command_writes_html_output(tmp_path: Path) -> None:
    html_output = tmp_path / "autogs.html"
    args = SimpleNamespace(
        workdir=str(tmp_path),
        env_file=".env",
        html_output=str(html_output),
        message=None,
        trait_name=None,
        phenotype_path=None,
        genotype_path=None,
    )

    exit_code = cmd_autogs(args)

    assert exit_code == 0
    assert html_output.exists()
    html = html_output.read_text(encoding="utf-8")
    assert "AutoGS" in html
    assert "Genomic Selection" in html
    assert "LargeWhite_Mini" in html
    assert "GWAS" not in html


def test_autogs_command_runs_autonomous_plan_and_workflow(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    pheno = tmp_path / "LargeWhite_Mini.csv"
    geno = tmp_path / "LargeWhite_Mini.vcf"
    pheno.write_text("animal_id,Backfat\nLW-2031,12.1\n", encoding="utf-8")
    geno.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_API_KEY", "secret-key")
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_MODEL", "deepseek-chat")

    calls = {"request_json": 0, "workflow_executor": 0}

    def fake_request_json(self, system_prompt, user_prompt):
        calls["request_json"] += 1
        if "对话路由器" in system_prompt:
            return {
                "intent": "gs_task",
                "reply": "",
                "trait_name": "Backfat",
                "phenotype_path": str(pheno),
                "genotype_path": str(geno),
            }
        return {
            "request_scope": "supported_gs",
            "trait_name": "Backfat",
            "user_goal": "rank candidates by GEBV",
            "candidate_fixed_effects": ["sex", "batch"],
            "population_description": "Large White pig population",
            "missing_inputs": [],
            "confidence": 0.94,
            "clarification_needed": False,
        }

    class FakeCandidate:
        individual_id = "LW-2031"
        gebv = 1.4821
        rank = 1

    class FakeArtifact:
        artifact_path = str(tmp_path / "runs" / "job-autogs" / "reports" / "gs_report.html")

    class FakeReport:
        report_text = "AI report: LW-2031 is the priority candidate."
        top_candidates = [FakeCandidate()]
        html_report_artifact = FakeArtifact()

    def fake_executor(job):
        calls["workflow_executor"] += 1
        from animal_gs_agent.services.workflow_service import WorkflowExecutionResult

        result_dir = tmp_path / "runs" / job.job_id
        gblup_dir = result_dir / "gblup"
        gblup_dir.mkdir(parents=True)
        (gblup_dir / "gebv_predictions.csv").write_text(
            "individual_id,gebv,gebv_rank\nLW-2031,1.4821,1\n",
            encoding="utf-8",
        )
        (gblup_dir / "model_summary.txt").write_text(
            "metric::pearson: 0.712\nmetric::rmse: 0.184\n",
            encoding="utf-8",
        )
        return WorkflowExecutionResult(
            backend="native_nextflow",
            command=["nextflow", "run", "main.nf"],
            result_dir=str(result_dir),
            status="completed",
        )

    monkeypatch.setattr("animal_gs_agent.cli.OpenAICompatibleLLMClient.request_json", fake_request_json)
    monkeypatch.setattr("animal_gs_agent.cli.execute_fixed_workflow", fake_executor)
    monkeypatch.setattr("animal_gs_agent.cli.build_job_report", lambda job: FakeReport())

    args = SimpleNamespace(
        workdir=str(tmp_path),
        env_file=".env",
        html_output=None,
        message="Perform Genomic Selection analysis on LargeWhite_Mini focusing on Backfat",
        trait_name=None,
        phenotype_path=None,
        genotype_path=None,
    )

    exit_code = cmd_autogs(args)

    assert exit_code == 0
    assert calls["request_json"] == 2
    assert calls["workflow_executor"] == 1
    output = capsys.readouterr().out
    assert "AutoGS (Agent): Processing request" in output
    assert "[Planner] Intent identified: Genomic Selection" in output
    assert "Candidate model pool: GBLUP" in output
    assert "Selected model:" in output
    assert "[Coder] Executing workflow" in output
    assert "Analysis completed successfully" in output
    assert "LW-2031" in output
    assert "gs_report.html" in output


def test_autogs_autonomous_run_requires_ai_configuration(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.delenv("ANIMAL_GS_AGENT_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("ANIMAL_GS_AGENT_LLM_API_KEY", raising=False)
    monkeypatch.delenv("ANIMAL_GS_AGENT_LLM_MODEL", raising=False)

    args = SimpleNamespace(
        workdir=str(tmp_path),
        env_file=".env",
        html_output=None,
        message="Perform Genomic Selection analysis on LargeWhite_Mini focusing on Backfat",
        trait_name="Backfat",
        phenotype_path="/tmp/LargeWhite_Mini.pheno",
        genotype_path="/tmp/LargeWhite_Mini.vcf",
    )

    exit_code = cmd_autogs(args)

    assert exit_code == 2
    output = capsys.readouterr().out
    assert "AI 未接入" in output
    assert "workflow" not in output.lower()


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


def test_prompt_text_temporarily_sets_tty_erase_to_ctrl_h(monkeypatch) -> None:
    class FakeStdin:
        encoding = "utf-8"
        buffer = io.BytesIO(b"hello\n")

        def fileno(self) -> int:
            return 123

        def isatty(self) -> bool:
            return True

    old_cc = [b"\x00"] * 32
    old_cc[1] = b"\x7f"
    old_attrs = [0, 0, 0, 0, 0, 0, old_cc]
    calls = []

    def fake_tcsetattr(fd, when, attrs):
        calls.append((fd, when, attrs))

    monkeypatch.setattr("sys.stdin", FakeStdin())
    monkeypatch.setattr("animal_gs_agent.cli.termios.VERASE", 1)
    monkeypatch.setattr("animal_gs_agent.cli.termios.TCSANOW", 0)
    monkeypatch.setattr("animal_gs_agent.cli.termios.ECHOE", 16)
    monkeypatch.setattr("animal_gs_agent.cli.termios.tcgetattr", lambda fd: old_attrs)
    monkeypatch.setattr("animal_gs_agent.cli.termios.tcsetattr", fake_tcsetattr)

    assert _prompt_text("你") == "hello"
    assert calls[0][0] == 123
    assert calls[0][2][6][1] == b"\x08"
    assert calls[0][2][3] & 16
    assert calls[1] == (123, 0, old_attrs)


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


def test_chat_lists_current_directory_when_ai_routes_tool(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    (tmp_path / "pheno.csv").write_text("animal_id,trait\nA1,1.0\n", encoding="utf-8")
    (tmp_path / "inputs").mkdir()
    calls = {"create_job": 0}
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_API_KEY", "secret-key")
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_MODEL", "deepseek-chat")
    monkeypatch.setattr(
        "animal_gs_agent.cli.OpenAICompatibleLLMClient.request_json",
        lambda self, system_prompt, user_prompt: {
            "intent": "list_files",
            "reply": "",
            "trait_name": "",
            "phenotype_path": "",
            "genotype_path": "",
        },
    )
    monkeypatch.setattr(
        "animal_gs_agent.cli.create_job",
        lambda *args, **kwargs: calls.__setitem__("create_job", calls["create_job"] + 1),
    )

    args = SimpleNamespace(
        workdir=str(tmp_path),
        env_file=".env",
        message="看下我当前目录下有什么文件",
        trait_name=None,
        phenotype_path=None,
        genotype_path=None,
    )

    exit_code = cmd_chat(args)

    assert exit_code == 0
    assert calls["create_job"] == 0
    output = capsys.readouterr().out
    assert "[gsagent] 当前目录:" in output
    assert "pheno.csv" in output
    assert "inputs/" in output
    assert "trait_name / 性状" not in output


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
