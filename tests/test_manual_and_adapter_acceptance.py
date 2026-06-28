from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_manual_and_adapter_acceptance_addendum_is_indexed_and_actionable() -> None:
    root = repo_root()
    overview = (root / "docs" / "spec-kit" / "00-overview.md").read_text(encoding="utf-8")
    roadmap = (root / "docs" / "spec-kit" / "13-next-improvements-roadmap.md").read_text(encoding="utf-8")
    report = (root / "docs" / "spec-kit" / "14-operational-acceptance-report.md").read_text(encoding="utf-8")
    addendum_path = root / "docs" / "spec-kit" / "15-manual-and-adapter-acceptance.md"
    addendum = addendum_path.read_text(encoding="utf-8")

    assert "15-manual-and-adapter-acceptance.md" in overview
    assert "15-manual-and-adapter-acceptance.md" in roadmap
    assert "15-manual-and-adapter-acceptance.md" in report

    required_sections = (
        "P1.3 Dashboard field review checklist",
        "P1.4 Diagram readability checklist",
        "P2.2 RAG/graph sandbox benchmark contract",
        "P2.3 MCP read-only adapter expansion contract",
        "Done criteria for this addendum",
    )
    for section in required_sections:
        assert section in addendum

    required_commands = (
        "pytest tests/test_phase07_review_dashboard_docs.py",
        "pytest tests/test_diagram_pdf_adapter.py",
        "python3 tools/obsidian_rag_graph_adapter.py",
        "pytest tests/test_rag_graph_adapter.py",
        "python3 tools/obsidian_mcp_adapter.py",
        "pytest tests/test_mcp_adapter.py",
    )
    for command in required_commands:
        assert command in addendum

    required_boundaries = (
        "does not approve live vault mutation",
        "disposable dashboard vault",
        "sandbox-only",
        "no direct write is enabled",
        "dangerous tools are refused",
        "executed=false",
    )
    for boundary in required_boundaries:
        assert boundary in addendum

    server_side_decisions = (
        "dashboard_visual_acceptance: accepted",
        "diagram_visual_acceptance: accepted",
        "Hermes Agent on server",
        "rendered flowchart",
        "rendered sequence diagram",
        "not source-preview fallback",
    )
    for decision in server_side_decisions:
        assert decision in addendum
