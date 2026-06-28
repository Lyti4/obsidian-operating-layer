from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_p3_telegram_summary_templates_are_safe_and_actionable() -> None:
    text = (repo_root() / "docs" / "telegram-summary-templates.md").read_text(encoding="utf-8")

    assert "Result first, evidence second" in text
    assert "Dmitry cannot inspect server files directly" in text
    assert "No secrets" in text
    assert "live vault was mutated" in text
    assert "Safe dry-run / proposal-only result" in text
    assert "Sandbox benchmark result" in text
    assert "Manual acceptance performed by Hermes on server" in text
    assert "Live apply request — approval required" in text
    assert "APPROVE OBSIDIAN APPLY" in text


def test_p3_make_aliases_are_documented_and_approval_gated() -> None:
    root = repo_root()
    makefile = (root / "Makefile").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")
    guide = (root / "docs" / "operator-guide.md").read_text(encoding="utf-8")
    roadmap = (root / "docs" / "spec-kit" / "13-next-improvements-roadmap.md").read_text(encoding="utf-8")

    for target in (
        "dashboard-list",
        "field-slice-example",
        "render-diagrams",
        "rag-benchmark",
        "mcp-benchmark",
    ):
        assert target in makefile
        assert f"make {target}" in readme
        assert f"make {target}" in guide
        assert target in roadmap

    assert "--apply" not in makefile
    assert "do not install cron" in readme
    assert "do not run real live apply" in readme
    assert "requires separate explicit approval" in guide
    assert "not installed; remains approval-gated" in roadmap
