from __future__ import annotations

import json
from pathlib import Path

import pytest

from obslayer.candidate_volume_operator_packet import (
    SAFETY,
    build_candidate_volume_operator_packet,
    write_candidate_volume_operator_packet,
)
from obslayer.guardrails import GuardrailError


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _source_artifacts(repo: Path) -> tuple[Path, Path, Path, Path]:
    observation = repo / "out" / "run" / "observation.json"
    proposal = repo / "out" / "run" / "propose" / "proposal.json"
    verify = repo / "out" / "run" / "verify.json"
    unified = repo / "out" / "reports" / "unified" / "unified-operator-review-index.json"
    _write_json(
        observation,
        {
            "vault_root": "/not/live/in/test",
            "observed_at": "2026-07-06T18:26:12+00:00",
            "file_counts": {".md": 3, ".json": 1},
            "protected_hits": [
                {"path": "_Backups/a.md"},
                {"path": "_Archive/b.md"},
                {"path": ".obsidian/app.json"},
                {"path": ".trash/deleted.md"},
                {"path": "Soul/private.md"},
                {"path": "Other/manual.md"},
            ],
            "sample_notes": ["A.md", "B.md"],
        },
    )
    _write_json(
        proposal,
        {
            "mode": "dry-run",
            "dry_run_default": True,
            "approval_required": True,
            "risk_class": "read_only_only",
            "targets": [],
        },
    )
    _write_json(verify, {"ok": True, "issues": []})
    _write_json(
        unified,
        {
            "status": "ready_for_operator_review",
            "summary": {
                "blocked_count": 0,
                "missing_artifacts": 1,
                "proposal_only_count": 3,
                "ready_for_human_review_count": 1,
            },
            "safety": SAFETY,
        },
    )
    return observation, proposal, verify, unified


def test_builds_ready_packet_with_fixed_inert_safety_and_route_buckets(tmp_path: Path) -> None:
    observation, proposal, verify, unified = _source_artifacts(tmp_path)

    packet = build_candidate_volume_operator_packet(
        repo=tmp_path,
        observation=observation,
        proposal=proposal,
        verify=verify,
        unified_index=unified,
    )
    payload = packet.to_dict()

    assert payload["mode"] == "obslayer.candidate-volume-operator-packet.v1"
    assert payload["status"] == "ready_for_operator_review"
    assert payload["safety"] == SAFETY
    for key, value in SAFETY.items():
        assert payload[key] == value
    assert payload["vault_root"] == "/not/live/in/test"
    assert payload["observed_at"] == "2026-07-06T18:26:12+00:00"
    assert payload["file_counts"] == {".md": 3, ".json": 1}
    assert payload["protected_hits_count"] == 6
    assert payload["protected_bucket_counts"] == {
        "_Backups": 1,
        "_Archive": 1,
        ".obsidian": 1,
        ".trash": 1,
        "Soul": 1,
        "other": 1,
    }
    assert payload["sample_notes_count"] == 2
    assert payload["proposal"]["targets_count"] == 0
    assert payload["verify"] == {"ok": True, "issues_count": 0}
    assert payload["unified"]["missing_count"] == 1
    assert payload["route_buckets"]["blocked"] == []
    assert payload["route_buckets"]["protected_manual_review"] == []
    assert payload["route_buckets"]["proposal_only_ready"] == ["proposal has no targets; operator volume checkpoint only"]
    assert payload["route_buckets"]["stale_missing_artifact_cleanup"] == [
        "unified index reports 1 missing artifact(s)"
    ]
    assert payload["route_buckets"]["first_manifest_candidate_queue"] == []


def test_blocks_when_any_input_claims_apply_or_manifest_authority(tmp_path: Path) -> None:
    observation, proposal, verify, unified = _source_artifacts(tmp_path)
    _write_json(proposal, {"targets": [], "live_mutation_authorized": "true", "apply_authority": "none"})

    packet = build_candidate_volume_operator_packet(
        repo=tmp_path,
        observation=observation,
        proposal=proposal,
        verify=verify,
        unified_index=unified,
    )

    assert packet.status == "blocked"
    assert packet.route_buckets["blocked"]
    assert packet.safety == SAFETY


def test_non_empty_proposal_targets_stay_manual_and_never_authorized(tmp_path: Path) -> None:
    observation, proposal, verify, unified = _source_artifacts(tmp_path)
    _write_json(
        proposal,
        {
            "mode": "dry-run",
            "dry_run_default": True,
            "approval_required": True,
            "risk_class": "review_required",
            "targets": [{"path": "Notes/a.md"}],
        },
    )

    packet = build_candidate_volume_operator_packet(
        repo=tmp_path,
        observation=observation,
        proposal=proposal,
        verify=verify,
        unified_index=unified,
    )

    payload = packet.to_dict()
    assert packet.status == "ready_for_operator_review"
    assert packet.safety["target_paths"] == []
    assert payload["target_paths"] == []
    assert packet.route_buckets["protected_manual_review"] == ["Notes/a.md"]
    assert packet.route_buckets["first_manifest_candidate_queue"] == []


def test_write_guard_rejects_output_outside_repo_and_symlink_escape(tmp_path: Path) -> None:
    observation, proposal, verify, unified = _source_artifacts(tmp_path)
    packet = build_candidate_volume_operator_packet(
        repo=tmp_path,
        observation=observation,
        proposal=proposal,
        verify=verify,
        unified_index=unified,
    )
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    with pytest.raises(GuardrailError):
        write_candidate_volume_operator_packet(packet, outside)

    link = tmp_path / "out" / "escape"
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(GuardrailError):
        write_candidate_volume_operator_packet(packet, link)

    json_path, report_path = write_candidate_volume_operator_packet(packet, tmp_path / "out" / "packet")
    assert json_path.name == "candidate-volume-operator-packet.json"
    assert report_path.name == "REPORT.md"
    assert "Candidate Volume Operator Packet" in report_path.read_text(encoding="utf-8")
