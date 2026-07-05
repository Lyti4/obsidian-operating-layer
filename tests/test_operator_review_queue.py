from pathlib import Path

from obslayer.operator_review_queue import build_operator_review_queue, operator_review_queue_to_markdown


def test_build_operator_review_queue_marks_existing_and_missing(tmp_path: Path) -> None:
    (tmp_path / "docs/spec-kit").mkdir(parents=True)
    (tmp_path / "docs/spec-kit/30-orchestrator-operating-spec.md").write_text("spec", encoding="utf-8")

    candidates = (
        {
            "id": "sample",
            "state": "review_ready",
            "title": "Sample",
            "evidence_paths": ["docs/spec-kit/30-orchestrator-operating-spec.md", "missing.md"],
            "next_step": "Review only.",
        },
    )
    queue = build_operator_review_queue(tmp_path, created_at="2026-07-04T00:00:00Z", candidates=candidates)

    assert queue.status == "ready-with-held-items"
    assert queue.live_mutation_authorized is False
    assert queue.approval_manifest_created is False
    assert queue.items[0].state == "held"
    assert queue.items[0].existing_evidence_paths == ["docs/spec-kit/30-orchestrator-operating-spec.md"]
    assert queue.items[0].missing_evidence_paths == ["missing.md"]


def test_operator_review_queue_markdown_states_no_live_authorization(tmp_path: Path) -> None:
    candidates = (
        {
            "id": "sample",
            "state": "proposal_drafted",
            "title": "Sample",
            "evidence_paths": [],
            "next_step": "Review | hold.",
        },
    )
    queue = build_operator_review_queue(tmp_path, created_at="2026-07-04T00:00:00Z", candidates=candidates)
    text = operator_review_queue_to_markdown(queue)

    assert "Operator Review Queue" in text
    assert "Live mutation authorized: `False`" in text
    assert "Queue state does not authorize live vault mutation" in text
    assert r"Review \| hold" in text


def test_operator_review_queue_mixed_home_relative_keeps_repo_paths_in_repo(tmp_path: Path) -> None:
    (tmp_path / "docs/spec-kit").mkdir(parents=True)
    (tmp_path / "docs/spec-kit/32-codex-hermes-communication-channel.md").write_text("spec", encoding="utf-8")
    candidates = (
        {
            "id": "codex",
            "state": "review_ready",
            "title": "Codex channel",
            "evidence_paths": ["docs/spec-kit/32-codex-hermes-communication-channel.md", ".missing-home-policy.json"],
            "next_step": "Review only.",
            "mixed_home_relative": True,
        },
    )

    queue = build_operator_review_queue(tmp_path, created_at="2026-07-04T00:00:00Z", candidates=candidates)

    assert queue.items[0].existing_evidence_paths == ["docs/spec-kit/32-codex-hermes-communication-channel.md"]
    assert queue.items[0].missing_evidence_paths == [".missing-home-policy.json"]
    assert queue.items[0].state == "held"


def test_default_operator_review_queue_includes_semantic_manifest_boundary(tmp_path: Path) -> None:
    required = [
        "docs/spec-kit/29-semantic-proposal-workflow.md",
        "docs/spec-kit/36-current-evidence-index.md",
        "docs/acceptance/index.md",
        "src/obslayer/semantic_manifest.py",
        "tools/obsidian_semantic_manifest.py",
        "tests/test_semantic_manifest.py",
        "out/reports/semantic-manifests/manual/semantic-manifest.json",
        "out/reports/semantic-manifests/manual/REPORT.md",
    ]
    for rel in required:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("evidence", encoding="utf-8")

    queue = build_operator_review_queue(tmp_path, created_at="2026-07-04T00:00:00Z")
    item = next(item for item in queue.items if item.id == "semantic-indexing-manifest")

    assert item.state == "ready_for_operator_review"
    assert item.live_mutation_authorized is False
    assert item.missing_evidence_paths == []
    assert "explicit approval" in item.next_step
