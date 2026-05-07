"""Workflow artifact listing helpers."""

from pathlib import Path

from animal_gs_agent.schemas.jobs import JobArtifact


def list_artifacts(result_dir: str) -> list[JobArtifact]:
    root = Path(result_dir)
    if not root.exists():
        raise FileNotFoundError(f"result directory not found: {result_dir}")

    artifacts: list[JobArtifact] = []
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        artifacts.append(
            JobArtifact(
                relative_path=str(path.relative_to(root)),
                size_bytes=path.stat().st_size,
            )
        )
    return artifacts
