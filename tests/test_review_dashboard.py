from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from obslayer import GuardrailError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from obsidian_review_dashboard import collect_pending_proposals, validate_dashboard_source  # noqa: E402


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_project_dashboard_source_validates() -> None:
    result = validate_dashboard_source(repo_root() / "docs" / "obsidian-review-dashboard" / "index.md")

    assert result["status"] == "ok"
    assert "proposed" in result["status_labels"]
    assert "needs-review" in result["status_labels"]
    assert result["checklist_items"] >= 5


def test_dashboard_validation_rejects_missing_write_policy(tmp_path: Path) -> None:
    dashboard = tmp_path / "index.md"
    dashboard.write_text(
        """---
status: proposed
---
# Dashboard
## Safety contract
## Status labels
`proposed` `needs-review` `applied` `rejected`
## Review queue
```dataview
FROM \"Hermes/Review\"
```
## Proposal index
FROM \"Hermes/Review/Proposals\"
## Report index
FROM \"Hermes/Reports\"
## Task index
## Manual review checklist
- [ ] one
- [ ] two
- [ ] three
- [ ] four
- [ ] five
""",
        encoding="utf-8",
    )

    with pytest.raises(GuardrailError, match="write_policy: proposal_only"):
        validate_dashboard_source(dashboard)


def test_collect_pending_proposals_filters_closed(tmp_path: Path) -> None:
    pending = tmp_path / "pending"
    pending.mkdir()
    closed = tmp_path / "closed"
    closed.mkdir()
    (pending / "proposal.json").write_text(
        json.dumps(
            {
                "proposal_id": "p1",
                "source_id": "test",
                "status": "needs-review",
                "risk_class": "read_only_only",
                "targets": [],
                "evidence": [],
                "approval_required": True,
                "dry_run_default": True,
            }
        ),
        encoding="utf-8",
    )
    (closed / "proposal.json").write_text(
        json.dumps(
            {
                "proposal_id": "p2",
                "status": "rejected",
                "approval_required": True,
                "dry_run_default": True,
            }
        ),
        encoding="utf-8",
    )

    rows = collect_pending_proposals(tmp_path)

    assert [row["proposal_id"] for row in rows] == ["p1"]


def test_explain_semantic_proposal_only_includes_candidates(tmp_path: Path) -> None:
    proposal = tmp_path / "proposal.json"
    proposal.write_text(
        json.dumps(
            {
                "mode": "semantic-query-proposal-only-report",
                "proposal_id": "semantic-p1",
                "status": "needs-review",
                "risk_class": "read_only_only",
                "approval_required": True,
                "dry_run_default": True,
                "live_mutation_authorized": False,
                "targets": [],
                "summary": {"candidate_paths": 2, "chunks_indexed": 5},
                "queries": ["link hygiene", "approval manifest"],
                "candidates": [
                    {
                        "path": "Memory-Vault/Hermes/Reports/A.md",
                        "best_score": 0.9,
                        "hit_count": 2,
                        "queries": ["link hygiene", "approval manifest"],
                        "chunks": [0, 1],
                    }
                ],
                "safety": {
                    "proposal_only": True,
                    "targets_empty": True,
                    "live_mutation_authorized": False,
                },
            }
        ),
        encoding="utf-8",
    )

    from obsidian_review_dashboard import explain_proposal, render_explanation_markdown

    explanation = explain_proposal(proposal)
    text = render_explanation_markdown(explanation)

    assert explanation["approval_phrase"] == "not applicable — proposal-only / no targets"
    assert explanation["semantic_candidate_count"] == 1
    assert "## Semantic review candidates" in text
    assert "Memory-Vault/Hermes/Reports/A.md" in text
    assert "Semantic candidates are review inputs only" in text
    assert "live mutation authorized: `False`" in text
