# AutoGS Terminal GS Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a screenshot-ready AutoGS terminal-style GS demo without changing the existing GS HTML report template.

**Architecture:** Create a small renderer module that owns the demo transcript and can export both plain terminal text and a static HTML screenshot page. Add a `gsagent autogs` command that prints the same GS transcript so the CLI and screenshot page stay consistent.

**Tech Stack:** Python CLI with `argparse`, static HTML/CSS, pytest unit tests.

---

### Task 1: Lock CLI Requirements With Tests

**Files:**
- Modify: `tests/unit/test_cli.py`

- [ ] **Step 1: Add tests before implementation**

```python
from animal_gs_agent.cli import cmd_autogs

def test_parser_contains_expected_subcommands() -> None:
    parser = build_parser()
    action = next(item for item in parser._actions if item.dest == "command")
    subcommands = set(action.choices.keys())
    assert {"preflight", "serve", "worker", "print-env", "llm-check", "configure", "init", "chat", "run", "autogs"}.issubset(subcommands)

def test_autogs_command_prints_gs_terminal_demo(tmp_path, capsys) -> None:
    args = SimpleNamespace(workdir=str(tmp_path), env_file=".env", html_output=None)
    assert cmd_autogs(args) == 0
    output = capsys.readouterr().out
    assert "AutoGS" in output
    assert "Breeding Intelligent Agent" in output
    assert "Genomic Selection" in output
    assert "LargeWhite_Mini" in output
    assert "Backfat" in output
    assert "GEBV" in output
    assert "GWAS" not in output
```

- [ ] **Step 2: Run test to verify failure**

Run: `.venv/bin/python -m pytest tests/unit/test_cli.py::test_parser_contains_expected_subcommands tests/unit/test_cli.py::test_autogs_command_prints_gs_terminal_demo -q`

Expected: fail because `cmd_autogs` and the `autogs` subcommand do not exist yet.

### Task 2: Implement Shared Renderer

**Files:**
- Create: `src/animal_gs_agent/services/autogs_terminal_demo.py`
- Create: `docs/examples/autogs_terminal_gs.html`

- [ ] **Step 1: Add renderer module**

Create functions:

```python
def render_autogs_terminal_text() -> str:
    return "\n".join(line.text for line in AUTOGS_GS_TERMINAL_LINES)

def render_autogs_terminal_html() -> str:
    return static HTML with the same transcript, styled like autogs.png
```

- [ ] **Step 2: Generate the static example**

Run a Python snippet importing `render_autogs_terminal_html()` and write:

`docs/examples/autogs_terminal_gs.html`

Expected: the page opens as a white terminal-style AutoGS GS demo suitable for screenshot.

### Task 3: Add CLI Command

**Files:**
- Modify: `src/animal_gs_agent/cli.py`
- Modify: `tests/unit/test_cli.py`

- [ ] **Step 1: Add command**

Implement:

```python
def cmd_autogs(args: argparse.Namespace) -> int:
    _prepare_runtime(workdir=args.workdir, env_file=args.env_file)
    print(render_autogs_terminal_text())
    if args.html_output:
        Path(args.html_output).write_text(render_autogs_terminal_html(), encoding="utf-8")
    return 0
```

- [ ] **Step 2: Wire parser**

Add:

```python
autogs = subparsers.add_parser("autogs", help="print screenshot-ready AutoGS GS terminal demo")
autogs.add_argument("--workdir", default=".")
autogs.add_argument("--env-file", default=".env")
autogs.add_argument("--html-output", default=None)
autogs.set_defaults(func=cmd_autogs)
```

### Task 4: Verify

**Files:**
- Test: `tests/unit/test_cli.py`
- Test: `src/animal_gs_agent/services/autogs_terminal_demo.py`
- Test: `docs/examples/autogs_terminal_gs.html`

- [ ] **Step 1: Run targeted tests**

Run: `.venv/bin/python -m pytest tests/unit/test_cli.py -q`

Expected: pass.

- [ ] **Step 2: Compile changed Python files**

Run: `.venv/bin/python -m compileall -q src/animal_gs_agent/cli.py src/animal_gs_agent/services/autogs_terminal_demo.py`

Expected: exit code 0.

- [ ] **Step 3: Check screenshot page content**

Run: `rg -n "AutoGS|Genomic Selection|LargeWhite_Mini|Backfat|GEBV|GWAS" docs/examples/autogs_terminal_gs.html`

Expected: GS terms exist and `GWAS` does not exist.
