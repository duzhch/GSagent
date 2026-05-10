from pathlib import Path


def test_install_script_prefers_python3_then_python_fallback() -> None:
    script_path = Path(__file__).resolve().parents[3] / "scripts" / "install_global_gsagent.sh"
    content = script_path.read_text(encoding="utf-8")

    assert "command -v python3" in content
    assert "exec python3 -m animal_gs_agent.cli" in content
    assert "elif command -v python" in content
    assert "exec python -m animal_gs_agent.cli" in content
