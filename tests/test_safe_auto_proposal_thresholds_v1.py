from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from obslayer.safe_auto_proposal_thresholds_v1 import (
    build_safe_auto_proposal_thresholds_packet,
    evaluate_candidate_packet_for_auto_proposal,
    write_safe_auto_proposal_thresholds_packet,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def auto_packet() -> dict:
    return {
        "source": "Memory-Vault/A.md",
        "old_link": "[[B]]",
        "route_hint": "auto-propose",
        "review_required": False,
        "hard_stop": False,
        "top_two_gap": 30,
        "reason_codes": ["candidate_scorer_evidence_only", "active_target_available", "exact_title_match"],
        "safety_flags": ["evidence_only", "no_live_apply"],
        "candidates": [
            {
                "path": "Memory-Vault/B.md",
                "confidence": 0.97,
                "reason_codes": ["active_target_available", "exact_title_match"],
                "safety_flags": [],
            }
        ],
    }


def test_auto_proposal_emits_only_dry_run_inert_fields() -> None:
    packet = build_safe_auto_proposal_thresholds_packet(
        {
            "packet_id": "candidate-scorer-v1-test",
            "scored_links": [auto_packet()],
        },
        packet_id="safe-auto-test",
        created_at="2026-07-05T00:00:00Z",
    )

    assert packet["mode"] == "repo-only/evidence-only"
    assert packet["behavior"] == "evidence-only"
    assert packet["live_mutation_authorized"] is False
    assert packet["approval_manifest_created"] is False
    assert packet["approval_manifest_authority"] is False
    assert packet["targets"] == []
    assert packet["apply_authority"] == "none"
    assert packet["summary"]["dry_run_proposals"] == 1
    assert packet["summary"]["held_for_review"] == 0

    proposal = packet["dry_run_proposals"][0]
    assert proposal["file"] == "Memory-Vault/A.md"
    assert proposal["old_link"] == "[[B]]"
    assert proposal["proposed_link"] == "Memory-Vault/B.md"
    assert proposal["confidence"] == 0.97
    assert proposal["policy_tag"] == "dry-run-auto-propose"
    assert proposal["rollback_key"].startswith("rollback:")
    assert proposal["live_mutation_authorized"] is False
    assert proposal["approval_manifest_created"] is False
    assert proposal["targets"] == []
    assert proposal["apply_authority"] == "none"


def test_review_archive_soul_and_ambiguous_candidates_are_held() -> None:
    sensitive = auto_packet()
    sensitive.update(
        {
            "route_hint": "needs-human-review",
            "review_required": True,
            "reason_codes": ["operator_review_required", "source_soul_surface"],
            "safety_flags": ["operator_review_required", "soul_policy_sensitive"],
        }
    )
    archive = auto_packet()
    archive["candidates"] = [
        {
            "path": "_Archive/B.md",
            "confidence": 0.99,
            "reason_codes": ["archive_shadow_target", "protected_or_archive_target"],
            "safety_flags": ["archive_or_shadow_target_hard_stop"],
        }
    ]
    archive["hard_stop"] = True

    packet = build_safe_auto_proposal_thresholds_packet({"scored_links": [sensitive, archive]})

    assert packet["dry_run_proposals"] == []
    assert packet["summary"]["held_for_review"] == 2
    assert {item["policy_tag"] for item in packet["held_for_review"]} == {"hold-for-human-review"}
    assert evaluate_candidate_packet_for_auto_proposal(sensitive)["eligible"] is False
    assert evaluate_candidate_packet_for_auto_proposal(archive)["eligible"] is False


def test_write_bundle_and_cli_smoke(tmp_path: Path) -> None:
    candidate_json = tmp_path / "candidate-scorer-v1.json"
    candidate_json.write_text(json.dumps({"packet_id": "candidate", "scored_links": [auto_packet()]}) + "\n", encoding="utf-8")
    result = write_safe_auto_proposal_thresholds_packet(candidate_scorer_json=candidate_json, out_dir=tmp_path / "out")

    packet = json.loads(Path(result["packet"]).read_text(encoding="utf-8"))
    assert packet["summary"]["dry_run_proposals"] == 1
    assert Path(result["proposals_jsonl"]).read_text(encoding="utf-8").strip()
    assert "dry-run proposal generator" in Path(result["report"]).read_text(encoding="utf-8")

    cli_out = subprocess.check_output(
        [
            sys.executable,
            str(repo_root() / "tools/obsidian_safe_auto_proposal_thresholds.py"),
            "--candidate-scorer-json",
            str(candidate_json),
            "--out-dir",
            str(tmp_path / "cli-out"),
        ],
        text=True,
    )
    assert json.loads(cli_out)["status"] == "ok"
