from pathlib import Path


def test_singularity_packaging_files_exist() -> None:
    root = Path(__file__).resolve().parents[3]
    assert (root / "packaging" / "singularity" / "Apptainer.def").exists()
    assert (root / "packaging" / "singularity" / "build_sif.sh").exists()
    assert (root / "packaging" / "singularity" / "run_examples.sh").exists()
    assert (root / "packaging" / "singularity" / "README.md").exists()


def test_apptainer_def_and_build_script_include_full_runtime_contract() -> None:
    root = Path(__file__).resolve().parents[3]
    definition = (root / "packaging" / "singularity" / "Apptainer.def").read_text(encoding="utf-8")
    build_script = (root / "packaging" / "singularity" / "build_sif.sh").read_text(encoding="utf-8")

    assert "packaging/runtime/environment.yml" in definition
    assert "python -m animal_gs_agent.cli" in definition
    assert "nextflow -version" in definition
    assert "plink2 --version" in definition
    assert "Rscript -e" in definition
    assert "ANIMAL_GS_AGENT_LLM_API_KEY" not in definition

    assert "apptainer" in build_script or "singularity" in build_script
    assert "Apptainer.def" in build_script
