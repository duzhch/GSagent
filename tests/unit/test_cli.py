from pathlib import Path
import os
from types import SimpleNamespace

import pytest

from animal_gs_agent.cli import (
    _prepare_runtime,
    _required_command_missing,
    _resolve_workdir,
    build_parser,
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
    assert {"preflight", "serve", "worker", "print-env", "llm-check", "configure", "init"}.issubset(
        subcommands
    )


def test_required_command_missing_accepts_python3_fallback(monkeypatch) -> None:
    available = {"python3", "nextflow", "plink2", "Rscript"}

    monkeypatch.setattr(
        "animal_gs_agent.cli.shutil.which",
        lambda cmd: f"/usr/bin/{cmd}" if cmd in available else None,
    )

    assert _required_command_missing() == []


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
    monkeypatch.setattr("animal_gs_agent.cli.getpass", lambda _: "sk-test-123")
    monkeypatch.setattr("animal_gs_agent.cli.secrets.token_urlsafe", lambda _: "token-demo")

    args = SimpleNamespace(workdir=str(tmp_path), env_file=".env")
    exit_code = cmd_configure(args)

    assert exit_code == 0
    env_content = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "ANIMAL_GS_AGENT_LLM_BASE_URL=https://api.deepseek.com" in env_content
    assert "ANIMAL_GS_AGENT_LLM_API_KEY=sk-test-123" in env_content
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
