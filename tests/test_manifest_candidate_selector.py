from __future__ import annotations

import json
from pathlib import Path

import pytest

from obslayer.guardrails import GuardrailError
from obslayer.manifest_candidate_selector import (
    SAFETY,
    build_manifest_candidate_selector,
    write_manifest_candidate_selector,
)


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _inputs(repo: Path) -> tuple[Path, Path, Path]:
    candidate_packet = _write_json(
        repo / "out" / "reports" / "candidate" / "candidate-volume-operator-packet.json",
        {
            "mode": "obslayer.candidate-volume-operator-packet.v1",
            "status": "ready_for_operator_review",
            "safety": SAFETY,
            **SAFETY,
        },
    )
    unified_index = _write_json(
        repo / "out" / "reports" / "unified" / "unified-operator-review-index.json",
        {
            "mode": "obslayer.unified-operator-review-index.v1",
            "status": "ready_for_operator_review",
            "summary": {"blocked_count": 0, "missing_artifacts": 0},
            "safety": SAFETY,
        },
    )
    operator_packet = _write_json(
        repo / "out" / "reports" / "operator" / "operator-review-packet.json",
        {
            "mode": "obslayer.operator-review-packet.v1",
            "status": "ready_for_human_review",
            "review_items": [
                {
                    "source_id": f"Note {index}.md#{index}",
                    "route": route,
                    "old_link": f"[[Old {index}]]",
                    "proposed_link": f"[[New {index}]]",
                    "rollback_key": f"rollback-{index}",
                    "policy_tag": "operator-review-required",
                    "reason_codes": ["strong_link_match"],
                    "confidence": 0.9,
                }
                for index, route in enumerate(
                    [
                        "proposal_candidate",
                        "suggest",
                        "proposal_only_ready",
                        "",
                        "proposal_candidate",
                        "proposal_candidate",
                    ],
                    start=1,
                )
            ],
            "safety": SAFETY,
        },
    )
    return candidate_packet, unified_index, operator_packet


def test_selects_at_most_five_inert_candidates(tmp_path: Path) -> None:
    candidate_packet, unified_index, operator_packet = _inputs(tmp_path)

    selector = build_manifest_candidate_selector(
        repo=tmp_path,
        candidate_packet=candidate_packet,
        unified_index=unified_index,
        operator_review_packet=operator_packet,
    )
    payload = selector.to_dict()

    assert payload["mode"] == "obslayer.manifest-candidate-selector.v1"
    assert payload["status"] == "ready_for_operator_review"
    assert payload["selected_count"] == 5
    assert len(payload["selected_candidates"]) == 5
    assert payload["manual_review_exclusions"] == []
    assert payload["safety"] == SAFETY
    for key, value in SAFETY.items():
        assert payload[key] == value
    assert all(candidate["approval_required"] is True for candidate in payload["selected_candidates"])
    assert all(candidate["apply_authority"] == "none" for candidate in payload["selected_candidates"])
    assert payload["selected_candidates"][3]["route"] == ""
    assert "separate explicit approval manifest is required" in payload["next_safe_step"]


def test_excludes_protected_and_denylisted_paths(tmp_path: Path) -> None:
    candidate_packet, unified_index, operator_packet = _inputs(tmp_path)
    payload = json.loads(operator_packet.read_text(encoding="utf-8"))
    payload["review_items"] = [
        {
            "source_id": ".obsidian/app.json#1",
            "route": "proposal_candidate",
            "old_link": "[[A]]",
            "proposed_link": "[[B]]",
        },
        {
            "source_id": "safe.md#2",
            "route": "proposal_candidate",
            "old_link": "[[A]]",
            "proposed_link": "[[secure/B]]",
        },
        {
            "source_id": "safe.md#3",
            "route": "proposal_candidate",
            "old_link": "[[A]]",
            "proposed_link": "[[B]]",
        },
    ]
    _write_json(operator_packet, payload)

    selector = build_manifest_candidate_selector(
        repo=tmp_path,
        candidate_packet=candidate_packet,
        unified_index=unified_index,
        operator_review_packet=operator_packet,
    )

    assert selector.status == "ready_for_operator_review"
    assert selector.selected_count == 1
    assert selector.selected_candidates[0]["source_id"] == "safe.md#3"
    assert [item["source_id"] for item in selector.manual_review_exclusions] == [
        ".obsidian/app.json#1",
        "safe.md#2",
    ]
    assert all(item["reasons"] for item in selector.manual_review_exclusions)



def test_excludes_protected_fallback_target_fields(tmp_path: Path) -> None:
    candidate_packet, unified_index, operator_packet = _inputs(tmp_path)
    payload = json.loads(operator_packet.read_text(encoding="utf-8"))
    payload["review_items"] = [
        {
            "source_id": "safe.md#1",
            "route": "proposal_candidate",
            "old_link": "[[A]]",
            "target": "[[browser profile vault]]",
        },
        {
            "source_id": "safe.md#2",
            "route": "proposal_candidate",
            "old_link": "[[A]]",
            "new_text": "[[.obsidian/secret]]",
        },
        {
            "source_id": "safe.md#3",
            "route": "proposal_candidate",
            "old_link": "[[A]]",
            "target": "[[Allowed Target]]",
        },
    ]
    _write_json(operator_packet, payload)

    selector = build_manifest_candidate_selector(
        repo=tmp_path,
        candidate_packet=candidate_packet,
        unified_index=unified_index,
        operator_review_packet=operator_packet,
    )

    assert selector.status == "ready_for_operator_review"
    assert selector.selected_count == 1
    assert selector.selected_candidates[0]["source_id"] == "safe.md#3"
    assert [item["source_id"] for item in selector.manual_review_exclusions] == [
        "safe.md#1",
        "safe.md#2",
    ]
    assert all(item["reasons"] for item in selector.manual_review_exclusions)

def test_blocks_on_authority_or_unified_blockers(tmp_path: Path) -> None:
    candidate_packet, unified_index, operator_packet = _inputs(tmp_path)
    payload = json.loads(candidate_packet.read_text(encoding="utf-8"))
    payload["safety"]["approval_manifest_created"] = True
    _write_json(candidate_packet, payload)

    selector = build_manifest_candidate_selector(
        repo=tmp_path,
        candidate_packet=candidate_packet,
        unified_index=unified_index,
        operator_review_packet=operator_packet,
    )

    assert selector.status == "blocked"
    assert selector.selected_count == 0
    assert any("approval_manifest_created" in finding for finding in selector.findings)

    payload = json.loads(candidate_packet.read_text(encoding="utf-8"))
    payload["safety"]["approval_manifest_created"] = False
    payload["safety"]["target_paths"] = ["Memory-Vault/unsafe.md"]
    _write_json(candidate_packet, payload)

    selector = build_manifest_candidate_selector(
        repo=tmp_path,
        candidate_packet=candidate_packet,
        unified_index=unified_index,
        operator_review_packet=operator_packet,
    )

    assert selector.status == "blocked"
    assert selector.selected_count == 0
    assert any("target_paths" in finding for finding in selector.findings)

    payload["safety"]["target_paths"] = []
    _write_json(candidate_packet, payload)
    unified = json.loads(unified_index.read_text(encoding="utf-8"))
    unified["summary"]["missing_artifacts"] = 1
    _write_json(unified_index, unified)

    selector = build_manifest_candidate_selector(
        repo=tmp_path,
        candidate_packet=candidate_packet,
        unified_index=unified_index,
        operator_review_packet=operator_packet,
    )
    assert selector.status == "blocked"
    assert selector.selected_count == 0
    assert "unified index reports 1 missing artifact(s)" in selector.findings


def test_no_candidate_when_no_selectable_items(tmp_path: Path) -> None:
    candidate_packet, unified_index, operator_packet = _inputs(tmp_path)
    payload = json.loads(operator_packet.read_text(encoding="utf-8"))
    payload["review_items"] = [{"source_id": "x", "route": "manual_review"}]
    _write_json(operator_packet, payload)

    selector = build_manifest_candidate_selector(
        repo=tmp_path,
        candidate_packet=candidate_packet,
        unified_index=unified_index,
        operator_review_packet=operator_packet,
    )

    assert selector.status == "no_candidate"
    assert selector.selected_count == 0


def test_write_guard_rejects_output_outside_repo_and_symlink_escape(tmp_path: Path) -> None:
    candidate_packet, unified_index, operator_packet = _inputs(tmp_path)
    selector = build_manifest_candidate_selector(
        repo=tmp_path,
        candidate_packet=candidate_packet,
        unified_index=unified_index,
        operator_review_packet=operator_packet,
    )
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    with pytest.raises(GuardrailError):
        write_manifest_candidate_selector(selector, outside)

    link = tmp_path / "out" / "escape"
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(GuardrailError):
        write_manifest_candidate_selector(selector, link)

    json_path, report_path = write_manifest_candidate_selector(selector, tmp_path / "out" / "reports" / "selector")
    assert json_path.name == "manifest-candidate-selector.json"
    assert report_path.name == "REPORT.md"
    assert "Manifest Candidate Selector" in report_path.read_text(encoding="utf-8")
