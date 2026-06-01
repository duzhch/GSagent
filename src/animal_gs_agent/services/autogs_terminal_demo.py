"""Screenshot-ready AutoGS terminal demo for the GS use case."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape


@dataclass(frozen=True)
class TerminalLine:
    text: str
    css_class: str = "line"


AUTOGS_GS_TERMINAL_LINES: tuple[TerminalLine, ...] = (
    TerminalLine("    _         _        ____ ____", "logo"),
    TerminalLine("   / \\  _   _| |_ ___ / ___/ ___|", "logo"),
    TerminalLine("  / _ \\| | | | __/ _ \\ |  _\\___ \\", "logo"),
    TerminalLine(" / ___ \\ |_| | || (_) | |_| |___) |", "logo"),
    TerminalLine("/_/   \\_\\__,_|\\__\\___/ \\____|____/", "logo"),
    TerminalLine("              Breeding Intelligent Agent", "tagline"),
    TerminalLine(""),
    TerminalLine("[System] Initializing AutoGS Kernel...", "system"),
    TerminalLine("[System] Loading Knowledge Base (Genetics, Statistics, Pig-BERT)...", "system"),
    TerminalLine("[System] Ready. Type your instruction below.", "system-ready"),
    TerminalLine(""),
    TerminalLine("2026-06-01 09:12:04,116 - AutoGS-Planner - INFO - Initializing Planner...", "timestamp"),
    TerminalLine("2026-06-01 09:12:04,146 - AutoGS-Coder - INFO - Initializing Coder...", "timestamp"),
    TerminalLine(""),
    TerminalLine("Human: Perform Genomic Selection analysis on LargeWhite_Mini focusing on Backfat", "human"),
    TerminalLine(""),
    TerminalLine("AutoGS (Agent): Processing request...", "agent"),
    TerminalLine("[Planner] Analyzing intent and retrieving knowledge...", "planner"),
    TerminalLine(
        "2026-06-01 09:12:08,612 - AutoGS-Planner - INFO - Parsing user query: "
        "'Perform Genomic Selection analysis on LargeWhite_Mini focusing on Backfat'",
        "timestamp",
    ),
    TerminalLine(
        "2026-06-01 09:12:08,616 - AutoGS-Planner - INFO - Generated Plan: "
        "{'task_type': 'GS', 'model': 'GBLUP', 'trait': 'Backfat', 'dataset': 'LargeWhite_Mini'}",
        "timestamp",
    ),
    TerminalLine("[Planner] Intent identified: Genomic Selection", "planner"),
    TerminalLine("[Planner] Strategy formulated:", "planner"),
    TerminalLine("    1. Load dataset: LargeWhite_Mini"),
    TerminalLine("    2. Quality Control (MAF > 0.01, missing rate < 0.1)"),
    TerminalLine("    3. Kinship Matrix: VanRaden Method"),
    TerminalLine("    4. Genomic Prediction Model: GBLUP for Backfat"),
    TerminalLine("    5. Rank candidate individuals by GEBV"),
    TerminalLine("    6. Generate candidate decision report"),
    TerminalLine(""),
    TerminalLine("[Coder] Generating Python execution code...", "coder"),
    TerminalLine("[Coder] Executing workflow...", "coder"),
    TerminalLine("2026-06-01 09:12:09,614 - AutoGS-Coder - INFO - Generating and executing code based on plan...", "timestamp"),
    TerminalLine("2026-06-01 09:12:09,616 - AutoGS-Core - INFO - Running QC on data/LargeWhite_Mini.vcf...", "timestamp"),
    TerminalLine("2026-06-01 09:12:09,616 - AutoGS-Core - INFO - Detected format: VCF", "timestamp"),
    TerminalLine("2026-06-01 09:12:09,616 - AutoGS-Core - INFO - Filtering variants with MAF < 0.01...", "timestamp"),
    TerminalLine("2026-06-01 09:12:09,616 - AutoGS-Core - INFO - Filtering samples with missing rate > 0.1...", "timestamp"),
    TerminalLine("2026-06-01 09:12:10,618 - AutoGS-Core - INFO - QC completed. Cleaned data saved to results/LargeWhite_Mini/Backfat/LargeWhite_Mini_clean", "timestamp"),
    TerminalLine("2026-06-01 09:12:10,618 - AutoGS-Core - INFO - Constructing G-Matrix using VanRaden method from results/LargeWhite_Mini/Backfat/LargeWhite_Mini_clean...", "timestamp"),
    TerminalLine("2026-06-01 09:12:11,619 - AutoGS-Core - INFO - G-Matrix constructed and saved to results/LargeWhite_Mini/Backfat/LargeWhite_Mini_G.bin", "timestamp"),
    TerminalLine("2026-06-01 09:12:11,619 - AutoGS-Core - INFO - Starting Genomic Selection for trait: Backfat using GBLUP...", "timestamp"),
    TerminalLine("2026-06-01 09:12:12,120 - AutoGS-Core - INFO - 1. Loading genotype and phenotype data...", "timestamp"),
    TerminalLine("2026-06-01 09:12:12,621 - AutoGS-Core - INFO - 2. Checking population structure and fixed effects...", "timestamp"),
    TerminalLine("2026-06-01 09:12:12,922 - AutoGS-Core - INFO - 3. Fitting GBLUP genomic prediction model...", "timestamp"),
    TerminalLine("2026-06-01 09:12:13,621 - AutoGS-Core - INFO - 4. Cross-validation Pearson r: 0.712; RMSE: 0.184", "timestamp"),
    TerminalLine("2026-06-01 09:12:14,172 - AutoGS-Core - INFO - 5. Ranking 4,995 candidate individuals by GEBV...", "timestamp"),
    TerminalLine("2026-06-01 09:12:14,616 - AutoGS-Core - INFO - Genomic Selection completed. Results saved to results/LargeWhite_Mini/Backfat", "timestamp"),
    TerminalLine(""),
    TerminalLine("AutoGS (Agent): Analysis completed successfully!", "success"),
    TerminalLine("    ✓ Candidate ranking saved to: results/LargeWhite_Mini/Backfat/Backfat_candidates.csv", "success-path"),
    TerminalLine("    ✓ Model summary saved to: results/LargeWhite_Mini/Backfat/Backfat_model_summary.txt", "success-path"),
    TerminalLine("    ✓ Top candidate: LW-2031 (GEBV=1.4821)", "success-path"),
    TerminalLine("    ✓ Interactive HTML Report: results/LargeWhite_Mini/Backfat/Backfat_gs_report.html", "success-path"),
)


def render_autogs_terminal_text() -> str:
    """Return the plain terminal transcript used by the `gsagent autogs` command."""
    return "\n".join(line.text for line in AUTOGS_GS_TERMINAL_LINES)


def render_autogs_terminal_html() -> str:
    """Return a static HTML page that visually matches the AutoGS terminal screenshot."""
    rendered_lines = "\n".join(
        f'<span class="{line.css_class}">{escape(line.text)}</span>'
        for line in AUTOGS_GS_TERMINAL_LINES
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoGS Terminal - Genomic Selection Demo</title>
    <style>
        :root {{
            --magenta: #ff00df;
            --blue: #2865c8;
            --green: #0c8f19;
            --cyan: #057f9c;
            --ink: #222222;
            --muted: #555555;
        }}
        body {{
            margin: 0;
            background: #ffffff;
            color: var(--ink);
            font-family: "Courier New", Courier, monospace;
        }}
        .screen {{
            box-sizing: border-box;
            width: 1024px;
            min-height: 768px;
            padding: 20px 12px;
            background: #ffffff;
        }}
        .terminal {{
            margin: 0;
            white-space: pre-wrap;
            font-size: 10.5px;
            line-height: 1.05;
            letter-spacing: -0.25px;
        }}
        .terminal span {{
            display: block;
        }}
        .logo {{
            color: var(--magenta);
            font-size: 30px;
            line-height: 0.68;
            font-weight: 700;
            letter-spacing: -1.4px;
        }}
        .tagline {{
            color: var(--magenta);
            font-size: 10.5px;
            line-height: 1.05;
            font-weight: 700;
        }}
        .system {{ color: var(--blue); font-weight: 700; }}
        .system-ready {{ color: var(--green); font-weight: 700; }}
        .timestamp {{ color: var(--ink); }}
        .human {{ color: var(--ink); font-weight: 700; }}
        .agent {{ color: var(--magenta); font-weight: 700; }}
        .planner {{ color: var(--cyan); font-weight: 700; }}
        .coder {{ color: var(--blue); font-weight: 700; }}
        .success {{ color: var(--green); font-weight: 700; }}
        .success-path {{ color: var(--green); }}
        @media (max-width: 900px) {{
            .screen {{
                width: 100vw;
                min-height: 100vh;
                padding: 16px 12px;
            }}
            .terminal {{ font-size: 11px; }}
            .logo {{ font-size: 24px; }}
        }}
    </style>
</head>
<body>
    <main class="screen" aria-label="AutoGS terminal genomic selection demo">
        <pre class="terminal">{rendered_lines}</pre>
    </main>
</body>
</html>
"""
