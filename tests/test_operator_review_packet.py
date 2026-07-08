from __future__ import annotations

import json
from pathlib import Path

import pytest

from obslayer.guardrails import GuardrailError
from obslayer.operator_review_packet import (
    build_operator_review_packet,
    write_operator_review_packet,
)


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _safe_packet(**overrides: object) -> dict:
    payload = {
        "mode": "repo-only/evidence-only",
        "status": "ok",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "apply_authority": "none",
        "targets": [],
        "dry_run_proposals": [],
        "held_for_review": [],
    }
    payload.update(overrides)
    return payload


def test_no_candidate_packet_does_not_request_approval(tmp_path: Path) -> None:
    repo = tmp_path
    source = _write_json(repo / "out" / "proposal.json", _safe_packet(held_for_review=[{"id": "held-1"}]))

    packet = build_operator_review_packet(repo=repo, proposal_packet=source)

    assert packet.status == "no_candidate"
    assert packet.review_items == []
    assert packet.held_count == 1
    assert packet.safety["live_mutation_authorized"] is False
    assert packet.safety["approval_manifest_created"] is False
    assert packet.safety["apply_authority"] == "none"
    assert "do not request live approval" in packet.next_safe_step


def test_builds_ready_for_human_review_packet_from_dry_run_candidate(tmp_path: Path) -> None:
    repo = tmp_path
    source = _write_json(
        repo / "out" / "proposal.json",
        _safe_packet(
            dry_run_proposals=[
                {
                    "id": "p1",
                    "old_link": "[[Old]]",
                    "proposed_link": "[[New]]",
                    "confidence": 0.99,
                    "reason_codes": ["deterministic-high"],
                    "policy_tag": "safe-auto-proposal",
                    "rollback_key": "rb1",
                }
            ]
        ),
    )

    packet = build_operator_review_packet(repo=repo, proposal_packet="out/proposal.json")

    assert packet.status == "ready_for_human_review"
    assert len(packet.review_items) == 1
    item = packet.review_items[0]
    assert item.source_id == "p1"
    assert item.old_link == "[[Old]]"
    assert item.proposed_link == "[[New]]"
    assert item.confidence == 0.99
    assert packet.source_proposal_packet == str(source.resolve())


def test_builds_review_items_from_grouped_proposal_replacements(tmp_path: Path) -> None:
    repo = tmp_path
    source = _write_json(
        repo / "out" / "proposal.grouped.json",
        {
            "mode": "remaining-link-same-vault-rule-next5-v1-grouped",
            "vault_root": "/home/hermesadmin/Obsidian",
            "summary": {
                "logical_replacements": 2,
                "proposal_targets": 1,
                "live_mutation_authorized": False,
                "apply_authority": "none",
            },
            "targets": [
                {
                    "path": "Memory-Vault/00 Memory Graph Index.md",
                    "base_sha256": "abc123",
                    "evidence": {
                        "grouped_replacements": [
                            {
                                "old_text": "[[Old One]]",
                                "new_text": "[[Memory-Vault/Old One]]",
                                "evidence": {
                                    "source_decision": "proposal_candidate",
                                    "source_reason": "same-vault exact target",
                                },
                            },
                            {
                                "old_text": "[[Old Two]]",
                                "new_text": "[[Memory-Vault/Old Two]]",
                                "evidence": {
                                    "source_decision": "proposal_candidate",
                                    "source_reason": "same-vault exact target",
                                },
                            },
                        ]
                    },
                }
            ],
        },
    )

    packet = build_operator_review_packet(repo=repo, proposal_packet=source)

    assert packet.status == "ready_for_human_review"
    assert len(packet.review_items) == 2
    assert packet.review_items[0].source_id == "Memory-Vault/00 Memory Graph Index.md#1"
    assert packet.review_items[0].old_link == "[[Old One]]"
    assert packet.review_items[0].proposed_link == "[[Memory-Vault/Old One]]"
    assert packet.review_items[1].old_link == "[[Old Two]]"
    assert packet.safety["target_paths"] == []
    assert packet.safety["apply_authority"] == "none"
    assert packet.safety["live_mutation_authorized"] is False


def test_builds_review_items_from_manual_selector_packet(tmp_path: Path) -> None:
    repo = tmp_path
    source = _write_json(
        repo / "out" / "manual-review-selector-v1.json",
        {
            "schema": "obslayer.manual-review-selector.v1",
            "mode": "obslayer.manual-review-selector.v1",
            "packet_type": "manual_review_evidence_only",
            "status": "ready_for_manual_review",
            "live_mutation_authorized": False,
            "approval_manifest_created": False,
            "approval_manifest_authority": False,
            "apply_authority": "none",
            "targets": [],
            "review_items": [
                {
                    "old_link": "Hermes/00 Hermes Index",
                    "proposed_path": "Hermes/00 Hermes Index.md",
                    "confidence": 1.0,
                    "reason_codes": ["exact_path_match"],
                    "policy_tag": "manual-review-only",
                    "selection_mode": "direct_manual_review",
                    "apply_authority": "none",
                    "live_mutation_authorized": False,
                    "review_queue": {"item_id": "manual-review-only-abc"},
                }
            ],
        },
    )

    packet = build_operator_review_packet(repo=repo, proposal_packet=source, max_review_items=10)

    assert packet.status == "ready_for_human_review"
    assert packet.findings == []
    assert len(packet.review_items) == 1
    item = packet.review_items[0]
    assert item.source_id == "manual-review-only-abc"
    assert item.old_link == "[[Hermes/00 Hermes Index]]"
    assert item.proposed_link == "[[Hermes/00 Hermes Index]]"
    assert item.policy_tag == "manual-review-only"
    assert packet.safety["live_mutation_authorized"] is False
    assert packet.safety["apply_authority"] == "none"


def test_blocks_grouped_proposal_that_claims_apply_or_live_authority(tmp_path: Path) -> None:
    repo = tmp_path
    source = _write_json(
        repo / "out" / "proposal.grouped.json",
        {
            "mode": "remaining-link-same-vault-rule-next5-v1-grouped",
            "live_mutation_authorized": True,
            "apply_authority": "approved",
            "summary": {
                "live_mutation_authorized": True,
                "apply_authority": "approved",
            },
            "targets": [
                {
                    "path": "Memory-Vault/00 Memory Graph Index.md",
                    "evidence": {
                        "grouped_replacements": [
                            {
                                "old_text": "[[Old]]",
                                "new_text": "[[New]]",
                            }
                        ]
                    },
                }
            ],
        },
    )

    packet = build_operator_review_packet(repo=repo, proposal_packet=source)

    assert packet.status == "blocked"
    assert "source proposal packet must not authorize live mutation" in packet.findings
    assert "source proposal packet must not have apply authority" in packet.findings
    assert "source proposal packet summary must not authorize live mutation" in packet.findings
    assert "source proposal packet summary must not have apply authority" in packet.findings
    assert packet.safety["target_paths"] == []
    assert packet.safety["apply_authority"] == "none"


def test_blocks_source_packet_that_authorizes_live_mutation(tmp_path: Path) -> None:
    repo = tmp_path
    source = _write_json(repo / "out" / "proposal.json", _safe_packet(live_mutation_authorized=True))

    packet = build_operator_review_packet(repo=repo, proposal_packet=source)

    assert packet.status == "blocked"
    assert "live_mutation_authorized=false" in packet.findings[0]


def test_refuses_inputs_outside_repo_out(tmp_path: Path) -> None:
    outside = _write_json(tmp_path / "proposal.json", _safe_packet())
    repo = tmp_path / "repo"
    repo.mkdir()

    with pytest.raises(GuardrailError):
        build_operator_review_packet(repo=repo, proposal_packet=outside)


def test_writes_json_and_markdown_report(tmp_path: Path) -> None:
    repo = tmp_path
    source = _write_json(repo / "out" / "proposal.json", _safe_packet())
    packet = build_operator_review_packet(repo=repo, proposal_packet=source)

    json_path, report_path = write_operator_review_packet(packet, repo / "out" / "review")

    assert json_path.is_file()
    assert report_path.is_file()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["mode"] == "obslayer.operator-review-packet.v1"
    assert "live mutation authorized: `false`" in report_path.read_text(encoding="utf-8")
