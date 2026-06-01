from pathlib import Path


def test_static_autogs_terminal_gs_html_is_screenshot_ready() -> None:
    html_path = Path(__file__).resolve().parents[3] / "docs/examples/autogs_terminal_gs.html"

    assert html_path.exists()
    html = html_path.read_text(encoding="utf-8")
    assert "AutoGS" in html
    assert "Breeding Intelligent Agent" in html
    assert "Human: Perform Genomic Selection analysis on LargeWhite_Mini focusing on Backfat" in html
    assert "Genomic Selection" in html
    assert "LargeWhite_Mini" in html
    assert "Backfat" in html
    assert "GEBV" in html
    assert "Candidate ranking saved to:" in html
    assert "GWAS" not in html
