from pathlib import Path

from obslayer.project_docs_lag_audit import project_docs_lag_audit_to_markdown, run_project_docs_lag_audit


def _write_minimal_docs(repo: Path, *, include_marker: bool = True) -> None:
    docs = {
        "docs/spec-kit/26-nanobot-standing-worker.md": "every 15m\n212b7e8f3c21\nproject-state.json\n",
        "docs/spec-kit/24-orchestration-backlog.md": "Nanobot 15-minute audit loop\nevery 15m\nproject-state.json\n",
        "docs/spec-kit/29-semantic-proposal-workflow.md": (
            "tools/obsidian_semantic_review_index.py\nout/proposals/semantic-review-indexes/\nReview index step\n"
            "Semantic/indexing manifest step\ntools/obsidian_semantic_manifest.py\nout/reports/semantic-manifests/\n"
        ),
        "docs/acceptance/index.md": (
            "Semantic targeted proposal/review index\ntools/obsidian_semantic_review_index.py\n"
            "Semantic indexing manifest\ntools/obsidian_semantic_manifest.py\nno live mutation authorization\n"
            "Agentic OS control plane map\ndocs/spec-kit/35-agentic-os-control-plane-map.md\n"
            "docs/spec-kit/36-current-evidence-index.md\ndoes not authorize live mutation\n"
        ),
        "docs/spec-kit/28-global-headroom-only-llm-channel.md": (
            "docs/spec-kit/schemas/llm-channel.schema.json\nmake llm-channel-smoke\nmake llm-channel-smoke-live\n"
        ),
        "docs/spec-kit/35-agentic-os-control-plane-map.md": (
            "Control-plane surfaces\nQueue state model\nAcceptance gates\nCurrent Nanobot synthesis\n"
        ),
        "docs/spec-kit/36-current-evidence-index.md": (
            "Control-plane source surfaces\nCurrent generated evidence pointers\nSafety boundary\n"
        ),
        "AGENTS.md": "15 minutes\n212b7e8f3c21\nbounded read-only/proposal-only\n",
    }
    if not include_marker:
        docs["AGENTS.md"] = "212b7e8f3c21\nbounded read-only/proposal-only\n"
    for rel, text in docs.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def test_project_docs_lag_audit_ok(tmp_path: Path) -> None:
    _write_minimal_docs(tmp_path)

    audit = run_project_docs_lag_audit(tmp_path, generated_utc="2026-07-04T00:00:00Z")
    text = project_docs_lag_audit_to_markdown(audit)

    assert audit.status == "ok"
    assert all(check.status == "ok" for check in audit.checks)
    assert "Status: `ok`" in text
    assert "- none" in text


def test_project_docs_lag_audit_flags_missing_marker(tmp_path: Path) -> None:
    _write_minimal_docs(tmp_path, include_marker=False)

    audit = run_project_docs_lag_audit(tmp_path)

    assert audit.status == "lagging"
    assert any("operator_policy_mentions_15m_audit" in finding for finding in audit.findings)
    assert any("15 minutes" in check.missing_markers for check in audit.checks)
