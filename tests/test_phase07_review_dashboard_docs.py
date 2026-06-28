from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_review_dashboard_index_contains_dataview_statuses_and_safety_gate() -> None:
    dashboard = repo_root() / "docs" / "obsidian-review-dashboard" / "index.md"
    text = dashboard.read_text(encoding="utf-8")

    assert "```dataview" in text
    assert "Review queue" in text
    assert "Proposal index" in text
    assert "Report index" in text
    assert "Task index" in text
    for status in ("proposed", "needs-review", "applied", "rejected"):
        assert f"`{status}`" in text
    assert "approval manifest" in text
    assert "External workers must not write this note directly into a live vault" in text
    assert "Dashboard rows are review aids only; they are not approval manifests" in text


def test_review_note_template_is_templater_friendly_and_proposal_only() -> None:
    template = repo_root() / "docs" / "obsidian-review-dashboard" / "templates" / "review-note.md"
    text = template.read_text(encoding="utf-8")

    assert "<% tp.file.title %>" in text
    assert "<% tp.date.now('YYYY-MM-DD') %>" in text
    assert "status: needs-review" in text
    assert "write_policy: proposal_only" in text
    assert "valid status values" in text
    for status in ("proposed", "needs-review", "applied", "rejected"):
        assert status in text
    assert "No external worker wrote directly into the live vault" in text
    assert "approval manifest or explicit manual action" in text


def test_phase07_docs_do_not_reference_live_write_commands() -> None:
    docs_dir = repo_root() / "docs" / "obsidian-review-dashboard"
    combined = "\n".join(path.read_text(encoding="utf-8") for path in docs_dir.rglob("*.md"))

    forbidden_fragments = (
        "--apply",
        "obsidian_apply.py",
        "write-direct",
        "delete-direct",
        "move-direct",
    )
    for fragment in forbidden_fragments:
        assert fragment not in combined
    assert "proposal_only" in combined
    assert "out/" in combined
