from pathlib import Path


def _read_yaml(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_runtime_environment_includes_required_gs_tools() -> None:
    root = Path(__file__).resolve().parents[3]
    runtime_env = root / "packaging" / "runtime" / "environment.yml"
    native_env = root / "packaging" / "native" / "environment.yml"

    runtime_content = _read_yaml(runtime_env)
    native_content = _read_yaml(native_env)

    for content in (runtime_content, native_content):
        assert "nextflow" in content
        assert "plink2" in content
        assert "r-base" in content
        assert "r-jsonlite" in content
        assert "openjdk" in content


def test_runtime_bundle_builder_uses_runtime_environment_template() -> None:
    root = Path(__file__).resolve().parents[3]
    script_path = root / "packaging" / "runtime" / "build_cli_runtime_bundle.sh"
    content = script_path.read_text(encoding="utf-8")

    assert "packaging/runtime/environment.yml" in content
