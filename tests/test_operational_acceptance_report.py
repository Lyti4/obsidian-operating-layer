from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_operational_acceptance_report_is_indexed_and_names_evidence() -> None:
    root = repo_root()
    overview = (root / "docs" / "spec-kit" / "00-overview.md").read_text(encoding="utf-8")
    roadmap = (root / "docs" / "spec-kit" / "13-next-improvements-roadmap.md").read_text(encoding="utf-8")
    report_path = root / "docs" / "spec-kit" / "14-operational-acceptance-report.md"
    report = report_path.read_text(encoding="utf-8")

    assert "14-operational-acceptance-report.md" in overview
    assert "14-operational-acceptance-report.md" in roadmap

    required_sections = (
        "Controlled-autonomy report format clarity",
        "Disposable sandbox apply rehearsal",
        "Pending proposals command",
        "Human explanation for a proposal",
        "Dashboard field review",
        "Diagram readability acceptance",
        "Proposal-only field-test slice",
        "Remaining gaps",
        "Safety boundary",
    )
    for section in required_sections:
        assert section in report

    required_evidence = (
        "tools/obsidian_review_dashboard.py list",
        "tools/obsidian_review_dashboard.py explain",
        "tools/obsidian_field_slice.py",
        "tests/test_apply_rehearsal.py",
        "tests/test_controlled_autonomy.py",
        "tests/test_diagram_pdf_adapter.py",
        "tests/test_phase07_review_dashboard_docs.py",
        "make verify",
    )
    for evidence in required_evidence:
        assert evidence in report

    assert "real live apply" in report
    assert "explicit approval manifest" in report
    assert "Do not treat it as unsupervised production autonomy" in report
