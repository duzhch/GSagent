"""Command-line entrypoint for animal-gs-agent runtime operations."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import sys
import time

import uvicorn

from animal_gs_agent.services.worker_service import process_next_queued_job


def _resolve_workdir(path: str) -> Path:
    candidate = Path(path).expanduser().resolve()
    if not candidate.exists():
        raise FileNotFoundError(f"workdir does not exist: {candidate}")
    if not candidate.is_dir():
        raise NotADirectoryError(f"workdir is not a directory: {candidate}")
    return candidate


def _load_dotenv(env_path: Path) -> None:
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def _prepare_runtime(*, workdir: str, env_file: str) -> Path:
    resolved = _resolve_workdir(workdir)
    os.chdir(resolved)
    _load_dotenv(resolved / env_file)
    os.environ["ANIMAL_GS_AGENT_WORKDIR"] = str(resolved)
    return resolved


def _required_command_missing() -> list[str]:
    missing: list[str] = []
    for cmd in ("python", "nextflow", "plink2", "Rscript"):
        if shutil.which(cmd) is None:
            missing.append(cmd)
    return missing


def _required_env_missing() -> list[str]:
    missing: list[str] = []
    for name in (
        "ANIMAL_GS_AGENT_LLM_BASE_URL",
        "ANIMAL_GS_AGENT_LLM_API_KEY",
        "ANIMAL_GS_AGENT_LLM_MODEL",
    ):
        if not os.getenv(name, "").strip():
            missing.append(name)
    return missing


def cmd_preflight(args: argparse.Namespace) -> int:
    workdir = _prepare_runtime(workdir=args.workdir, env_file=args.env_file)
    print(f"[gsagent] workdir={workdir}")

    missing_cmd = _required_command_missing()
    missing_env = _required_env_missing()
    if missing_cmd:
        print("[gsagent] missing commands:", ", ".join(missing_cmd))
    if missing_env:
        print("[gsagent] missing env vars:", ", ".join(missing_env))

    if missing_cmd or missing_env:
        return 1
    print("[gsagent] preflight OK")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    _prepare_runtime(workdir=args.workdir, env_file=args.env_file)
    app_ref = "animal_gs_agent.api.app:create_app"
    print(f"[gsagent] starting API: {app_ref} host={args.host} port={args.port}")
    uvicorn.run(app_ref, factory=True, host=args.host, port=args.port, reload=args.reload)
    return 0


def cmd_worker(args: argparse.Namespace) -> int:
    _prepare_runtime(workdir=args.workdir, env_file=args.env_file)
    print(
        "[gsagent] starting worker "
        f"once={args.once} interval={args.interval_seconds}s"
    )
    if args.once:
        result = process_next_queued_job()
        print("[gsagent] worker result:", result.model_dump_json())
        return 0

    while True:
        result = process_next_queued_job()
        if result.processed:
            print("[gsagent] worker result:", result.model_dump_json())
        else:
            print("[gsagent] idle")
            time.sleep(args.interval_seconds)


def cmd_print_env(args: argparse.Namespace) -> int:
    workdir = _prepare_runtime(workdir=args.workdir, env_file=args.env_file)
    keys = [
        "ANIMAL_GS_AGENT_WORKDIR",
        "ANIMAL_GS_AGENT_LLM_BASE_URL",
        "ANIMAL_GS_AGENT_LLM_MODEL",
        "ANIMAL_GS_AGENT_WORKFLOW_EXECUTION_POLICY",
        "ANIMAL_GS_AGENT_RUN_QUEUE_SQLITE_PATH",
        "ANIMAL_GS_AGENT_JOB_STORE_SQLITE_PATH",
    ]
    print(f"[gsagent] workdir={workdir}")
    for key in keys:
        print(f"{key}={os.getenv(key, '')}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gsagent",
        description="Animal GS Agent command-line runtime",
    )
    parser.add_argument("--version", action="version", version="animal-gs-agent 0.1.0")
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight = subparsers.add_parser("preflight", help="validate runtime dependencies and env")
    preflight.add_argument("--workdir", default=".", help="working directory with .env and runtime files")
    preflight.add_argument("--env-file", default=".env", help="env file name in workdir")
    preflight.set_defaults(func=cmd_preflight)

    serve = subparsers.add_parser("serve", help="start FastAPI service")
    serve.add_argument("--workdir", default=".", help="working directory with .env and runtime files")
    serve.add_argument("--env-file", default=".env", help="env file name in workdir")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--reload", action="store_true", help="enable uvicorn reload")
    serve.set_defaults(func=cmd_serve)

    worker = subparsers.add_parser("worker", help="start async queue worker")
    worker.add_argument("--workdir", default=".", help="working directory with .env and runtime files")
    worker.add_argument("--env-file", default=".env", help="env file name in workdir")
    worker.add_argument("--once", action="store_true", help="process only one queued job")
    worker.add_argument("--interval-seconds", type=float, default=2.0)
    worker.set_defaults(func=cmd_worker)

    print_env = subparsers.add_parser("print-env", help="print effective runtime env values")
    print_env.add_argument("--workdir", default=".", help="working directory with .env and runtime files")
    print_env.add_argument("--env-file", default=".env", help="env file name in workdir")
    print_env.set_defaults(func=cmd_print_env)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    func = args.func
    return func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
