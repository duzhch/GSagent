from pathlib import Path


def test_native_delivery_layout_exists() -> None:
    root = Path(__file__).resolve().parents[3]
    required = [
        "packaging/native/environment.yml",
        "packaging/native/.env.example",
        "packaging/native/README.md",
        "scripts/native/preflight.sh",
        "scripts/native/start_api.sh",
        "scripts/native/demo_run.sh",
        "scripts/native/worker_loop.py",
        "docs/delivery/REAL_DATA_RUNBOOK.md",
        "docs/delivery/DEMO_10MIN_SCRIPT.md",
        "docs/delivery/MVP_ACCEPTANCE_CHECKLIST.md",
    ]

    missing = [item for item in required if not (root / item).exists()]
    assert missing == []
