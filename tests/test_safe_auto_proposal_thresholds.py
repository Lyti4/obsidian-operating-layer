from __future__ import annotations

import json
from pathlib import Path

from obslayer.candidate_scorer_v1 import score_candidate
from obslayer.safe_auto_proposal_thresholds import (
    build_safe_auto_proposal_bundle,
    serialize_safe_auto_proposal_bundle,
    write_safe_auto_proposal_bundle,
)


def _safe_packet() -> dict:
    packet = score_candidate(
        link={
            "source": "Memory-Vault/A.md",
            "status": "ok",
            "old_link": "[[B]]",
            "candidates": ["Memory-Vault/B.md"],
        },
        notes_by_path={
            "Memory-Vault/A.md": {"path": "Memory-Vault/A.md", "top": "Memory-Vault"},
            "Memory-Vault/B.md": {"path": "Memory-Vault/B.md", "top": "Memory-Vault"},
        },
    )
    packet["old_link"] = "[[B]]"
    packet["top_two_gap"] = 50
    return packet


def test_build_bundle_emits_only_evidence_only_dry_run_items() -> None:
    bundle = build_safe_auto_proposal_bundle(
        [_safe_packet()],
        bundle_id="bundle-test",
        created_at="2026-07-05T00:00:00Z",
        operator_decision_records=[{"decision_id": "prior-accepted", "decision_type": "accept-proposal"}],
    )
    payload = bundle.to_dict()

    assert payload["mode"] == "safe-auto-proposal-thresholds-v1"
    assert payload["live_mutation_authorized"] is False
    assert payload["approval_manifest_created"] is False
    assert payload["approval_manifest_authority"] is False
    assert payload["dry_run_only"] is True
    assert payload["targets"] == []
    assert payload["operator_decision_ledger_prior"] == {
        "authority": False,
        "behavior": "weak-evidence-only",
        "decision_ids": ["prior-accepted"],
        "record_count": 1,
    }

    assert len(payload["proposal_items"]) == 1
    item = payload["proposal_items"][0]
    assert item["source_path"] == "Memory-Vault/A.md"
    assert item["old_link_text"] == "[[B]]"
    assert item["proposed_target"] == "Memory-Vault/B.md"
    assert item["confidence"] == 1.0
    assert item["top_two_gap"] == 50
    assert item["policy_tag"] == "dry-run-safe-auto-proposal-thresholds"
    assert item["rollback_key"].startswith("rollback:")
    assert item["predicted_metric_delta"]["placeholder"] is True
    assert item["live_mutation_authorized"] is False
    assert item["approval_manifest_created"] is False
    assert payload["exclusions"] == []

    rendered = serialize_safe_auto_proposal_bundle(bundle)
    assert rendered.endswith("\n")
    assert json.loads(rendered)["bundle_id"] == "bundle-test"


def test_bundle_hard_stops_archive_duplicate_redirect_and_missing_candidates() -> None:
    scored = score_candidate(
        link={
            "source": "Memory-Vault/A.md",
            "status": "ok",
            "candidates": [
                "_Archive/B.md",
                "Duplicates/B copy.md",
                "Redirects/B.md",
                "Memory-Vault/Missing.md",
            ],
        },
        notes_by_path={
            "Memory-Vault/A.md": {"path": "Memory-Vault/A.md", "top": "Memory-Vault"},
            "_Archive/B.md": {"path": "_Archive/B.md", "top": "_Archive", "protected_or_archive_surface": True},
            "Duplicates/B copy.md": {"path": "Duplicates/B copy.md", "top": "Duplicates"},
            "Redirects/B.md": {"path": "Redirects/B.md", "top": "Redirects", "canonical_path": "Memory-Vault/B.md"},
        },
    )
    scored["top_two_gap"] = 50

    payload = build_safe_auto_proposal_bundle([scored]).to_dict()

    assert payload["proposal_items"] == []
    assert len(payload["exclusions"]) == 1
    exclusion = payload["exclusions"][0]
    assert "protected_or_archive_collision" in exclusion["exclusion_reasons"]
    assert "review_or_hard_stop_required" in exclusion["exclusion_reasons"]
    assert "sensitive_surface_or_action" in exclusion["exclusion_reasons"]
    assert exclusion["live_mutation_authorized"] is False
    assert exclusion["approval_manifest_created"] is False


def test_bundle_excludes_sensitive_surfaces_and_action_words_even_when_scored_high() -> None:
    packets = []
    for source, target in [
        ("Soul/Identity.md", "Memory-Vault/B.md"),
        ("Memory-Vault/A.md", "Memory-Vault/Rename Plan.md"),
        ("Memory-Vault/A.md", "Canonical/Global Index.md"),
    ]:
        packet = _safe_packet()
        packet["source"] = source
        packet["candidates"][0]["path"] = target
        packets.append(packet)

    payload = build_safe_auto_proposal_bundle(packets).to_dict()

    assert payload["proposal_items"] == []
    assert len(payload["exclusions"]) == 3
    assert all("sensitive_surface_or_action" in item["exclusion_reasons"] for item in payload["exclusions"])


def test_bundle_rejects_attempted_live_or_manifest_authority() -> None:
    packet = _safe_packet()
    packet["live_mutation_authorized"] = True
    packet["approval_manifest_created"] = True

    payload = build_safe_auto_proposal_bundle([packet]).to_dict()

    assert payload["proposal_items"] == []
    assert payload["exclusions"][0]["exclusion_reasons"] == [
        "input_attempted_approval_manifest_authority",
        "input_attempted_live_mutation_authority",
    ]


def test_write_bundle_outputs_json_and_markdown(tmp_path: Path) -> None:
    result = write_safe_auto_proposal_bundle([_safe_packet()], out_dir=tmp_path, bundle_id="write-test")

    assert result == {
        "status": "ok",
        "bundle": str(tmp_path / "proposal-bundle.json"),
        "report": str(tmp_path / "proposal-bundle.md"),
    }
    data = json.loads((tmp_path / "proposal-bundle.json").read_text(encoding="utf-8"))
    assert data["bundle_id"] == "write-test"
    assert data["approval_manifest_authority"] is False
    assert "Safe auto proposal thresholds" in (tmp_path / "proposal-bundle.md").read_text(encoding="utf-8")
