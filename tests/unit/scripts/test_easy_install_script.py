from pathlib import Path


def test_easy_install_script_bootstraps_runtime_and_global_launcher() -> None:
    script_path = Path(__file__).resolve().parents[3] / "scripts" / "install_easy_gsagent.sh"
    content = script_path.read_text(encoding="utf-8")

    assert "packaging/native/environment.yml" in content
    assert "Miniforge3-" in content
    assert "conda env create" in content or "env create" in content
    assert "conda run -n" in content
    assert "nextflow -version" in content
    assert "plink2 --version" in content
    assert "Rscript -e" in content
    assert "python -m animal_gs_agent.cli" in content
