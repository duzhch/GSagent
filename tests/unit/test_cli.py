from pathlib import Path
import os

import pytest

from animal_gs_agent.cli import _prepare_runtime, _resolve_workdir, build_parser


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
    assert {"preflight", "serve", "worker", "print-env", "llm-check"}.issubset(subcommands)
