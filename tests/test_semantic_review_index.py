import json
from pathlib import Path

import pytest

from obslayer.guardrails import GuardrailError
from obslayer.semantic_review_index import build_semantic_review_index, semantic_review_index_to_markdown


def _proposal(path: Path, **overrides) -> Path:
    payload = {
        "mode": "semantic-targeted-proposal",
        "group": "link_hygiene_reports",
        "candidate_paths": ["Memory-Vault/Hermes/Reports/A.md", "Memory-Vault/Hermes/Reports/B | C.md"],
        "targets": [],
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "safety": {"proposal_only": True},
    }
    payload.update(overrides)
    p = path / "proposal.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def test_build_semantic_review_index(tmp_path: Path) -> None:
    report = build_semantic_review_index(_proposal(tmp_path), created_at="2026-07-04T00:00:00Z")
    text = semantic_review_index_to_markdown(report)

    assert report.status == "ready-for-operator-review"
    assert report.item_count == 2
    assert report.live_mutation_authorized is False
    assert report.approval_manifest_created is False
    assert "Memory-Vault/Hermes/Reports/B \\| C.md" in text
    assert "does not authorize live vault edits" in text


def test_refuses_targeted_proposal_with_targets(tmp_path: Path) -> None:
    proposal = _proposal(tmp_path, targets=[{"path": "live.md"}])

    with pytest.raises(GuardrailError, match="no edit targets"):
        build_semantic_review_index(proposal)


def test_refuses_live_mutation_authorized(tmp_path: Path) -> None:
    proposal = _proposal(tmp_path, live_mutation_authorized=True)

    with pytest.raises(GuardrailError, match="live mutation must be false"):
        build_semantic_review_index(proposal)
