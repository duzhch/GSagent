"""Command-line entrypoint for animal-gs-agent runtime operations."""

from __future__ import annotations

import argparse
from getpass import getpass
import os
from pathlib import Path
import secrets
import shutil
import sys
import time

import uvicorn

from animal_gs_agent.config import LLMSettings, get_settings
from animal_gs_agent.llm.client import OpenAICompatibleLLMClient
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
    required_groups: list[tuple[str, ...]] = [
        ("python3", "python"),
        ("nextflow",),
        ("plink2",),
        ("Rscript",),
    ]
    for choices in required_groups:
        if not any(shutil.which(cmd) for cmd in choices):
            missing.append("/".join(choices))
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


def _prompt_text(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    raw = input(f"{label}{suffix}: ").strip()
    if raw:
        return raw
    return default or ""


def _prompt_secret(label: str) -> str:
    return getpass(f"{label}: ").strip()


def _read_env_kv(env_path: Path) -> dict[str, str]:
    if not env_path.exists():
        return {}
    values: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip("'").strip('"')
    return values


def _upsert_env_file(env_path: Path, updates: dict[str, str]) -> None:
    existing_lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    replaced: set[str] = set()
    output_lines: list[str] = []

    for line in existing_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            output_lines.append(line)
            continue
        key, _ = stripped.split("=", 1)
        key = key.strip()
        if key in updates:
            output_lines.append(f"{key}={updates[key]}")
            replaced.add(key)
        else:
            output_lines.append(line)

    missing = [key for key in updates if key not in replaced]
    if missing and output_lines and output_lines[-1].strip():
        output_lines.append("")
    for key in missing:
        output_lines.append(f"{key}={updates[key]}")

    env_path.write_text("\n".join(output_lines).rstrip() + "\n", encoding="utf-8")


def _collect_llm_settings(interactive: bool) -> LLMSettings:
    current = get_settings().llm
    base_url = current.base_url or ""
    api_key = current.api_key or ""
    model = current.model or ""

    if interactive:
        if not base_url:
            base_url = _prompt_text("LLM base_url", "https://api.deepseek.com")
        if not api_key:
            api_key = _prompt_text("LLM api_key", "")
        if not model:
            model = _prompt_text("LLM model", "deepseek-chat")

    return LLMSettings(
        base_url=base_url or None,
        api_key=api_key or None,
        model=model or None,
        timeout_seconds=current.timeout_seconds,
    )


def _run_llm_check(*, interactive: bool, prompt_message: str | None = None) -> tuple[bool, str]:
    settings = _collect_llm_settings(interactive=interactive)
    missing = []
    if not settings.base_url:
        missing.append("ANIMAL_GS_AGENT_LLM_BASE_URL")
    if not settings.api_key:
        missing.append("ANIMAL_GS_AGENT_LLM_API_KEY")
    if not settings.model:
        missing.append("ANIMAL_GS_AGENT_LLM_MODEL")
    if missing:
        return False, f"missing llm settings: {', '.join(missing)}"

    probe = prompt_message or "ping"
    if interactive and prompt_message is None:
        probe = _prompt_text("LLM 检查消息", "ping")

    client = OpenAICompatibleLLMClient(settings=settings)
    system_prompt = "Return strict JSON object with keys ok(bool) and echo(string)."
    user_prompt = f"health check message: {probe}"
    try:
        payload = client.request_json(system_prompt=system_prompt, user_prompt=user_prompt)
        if not isinstance(payload, dict):
            return False, "llm response is not a json object"
        ok = bool(payload.get("ok", True))
        echo = str(payload.get("echo", ""))
        if not ok:
            return False, f"llm provider returned ok=false echo={echo}"
        return True, f"ok echo={echo}"
    except Exception as exc:
        return False, str(exc)


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
    if args.llm_check != "skip":
        run_check = args.llm_check == "always"
        if args.llm_check == "auto":
            answer = _prompt_text("启动前检查大模型 API 是否可用? (y/n)", "y").lower()
            run_check = answer in {"", "y", "yes"}
        if run_check:
            ok, message = _run_llm_check(interactive=True, prompt_message=args.llm_probe)
            if ok:
                print(f"[gsagent] llm-check passed: {message}")
            else:
                print(f"[gsagent] llm-check failed: {message}")
                return 2

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


def cmd_llm_check(args: argparse.Namespace) -> int:
    _prepare_runtime(workdir=args.workdir, env_file=args.env_file)
    ok, message = _run_llm_check(interactive=True, prompt_message=args.message)
    if ok:
        print(f"[gsagent] llm-check passed: {message}")
        return 0
    print(f"[gsagent] llm-check failed: {message}")
    return 2


def cmd_configure(args: argparse.Namespace) -> int:
    workdir = _resolve_workdir(args.workdir)
    env_path = workdir / args.env_file
    existing = _read_env_kv(env_path)

    current_base_url = existing.get("ANIMAL_GS_AGENT_LLM_BASE_URL", "https://api.deepseek.com")
    current_model = existing.get("ANIMAL_GS_AGENT_LLM_MODEL", "deepseek-chat")
    current_api_token = existing.get("ANIMAL_GS_AGENT_API_TOKEN", secrets.token_urlsafe(32))
    current_policy = existing.get("ANIMAL_GS_AGENT_WORKFLOW_EXECUTION_POLICY", "auto")
    current_pipeline_dir = existing.get(
        "ANIMAL_GS_AGENT_WORKFLOW_PIPELINE_DIR",
        str(workdir / "pipeline"),
    )
    current_output_root = existing.get(
        "ANIMAL_GS_AGENT_WORKFLOW_OUTPUT_ROOT",
        str(workdir / "runs"),
    )
    current_submit_script = existing.get("ANIMAL_GS_AGENT_SLURM_SUBMIT_SCRIPT", "")
    current_allowed_roots = existing.get(
        "ANIMAL_GS_AGENT_ALLOWED_DATA_ROOTS",
        str((workdir.parent / "data").resolve()),
    )
    existing_api_key = existing.get("ANIMAL_GS_AGENT_LLM_API_KEY", "")

    base_url = _prompt_text("LLM base_url", current_base_url)
    model = _prompt_text("LLM model", current_model)
    api_key = _prompt_secret("LLM api_key (input hidden, leave blank to keep existing)")
    if not api_key:
        api_key = existing_api_key
    api_token = _prompt_text("API auth token", current_api_token)
    execution_policy = _prompt_text("workflow execution policy", current_policy)
    pipeline_dir = _prompt_text("workflow pipeline dir", current_pipeline_dir)
    output_root = _prompt_text("workflow output root", current_output_root)
    submit_script = _prompt_text("slurm submit script", current_submit_script)
    allowed_roots = _prompt_text("allowed data roots (comma-separated)", current_allowed_roots)

    updates = {
        "ANIMAL_GS_AGENT_LLM_BASE_URL": base_url,
        "ANIMAL_GS_AGENT_LLM_API_KEY": api_key,
        "ANIMAL_GS_AGENT_LLM_MODEL": model,
        "ANIMAL_GS_AGENT_API_TOKEN": api_token,
        "ANIMAL_GS_AGENT_WORKFLOW_EXECUTION_POLICY": execution_policy,
        "ANIMAL_GS_AGENT_WORKFLOW_PIPELINE_DIR": pipeline_dir,
        "ANIMAL_GS_AGENT_WORKFLOW_OUTPUT_ROOT": output_root,
        "ANIMAL_GS_AGENT_SLURM_SUBMIT_SCRIPT": submit_script,
        "ANIMAL_GS_AGENT_ALLOWED_DATA_ROOTS": allowed_roots,
    }
    _upsert_env_file(env_path, updates)
    print(f"[gsagent] wrote configuration: {env_path}")
    print("[gsagent] next step: gsagent preflight --workdir", workdir)
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
    serve.add_argument(
        "--llm-check",
        choices=["auto", "always", "skip"],
        default="auto",
        help="startup llm api check mode",
    )
    serve.add_argument("--llm-probe", default=None, help="probe message for llm check")
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

    llm_check = subparsers.add_parser("llm-check", help="interactive llm api availability check")
    llm_check.add_argument("--workdir", default=".", help="working directory with .env and runtime files")
    llm_check.add_argument("--env-file", default=".env", help="env file name in workdir")
    llm_check.add_argument("--message", default=None, help="probe message for llm check")
    llm_check.set_defaults(func=cmd_llm_check)

    configure = subparsers.add_parser(
        "configure",
        aliases=["init"],
        help="interactive setup for API key/token and runtime .env",
    )
    configure.add_argument("--workdir", default=".", help="working directory with .env and runtime files")
    configure.add_argument("--env-file", default=".env", help="env file name in workdir")
    configure.set_defaults(func=cmd_configure)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    func = args.func
    return func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
