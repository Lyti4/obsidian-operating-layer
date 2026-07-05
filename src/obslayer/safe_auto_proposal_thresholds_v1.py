from __future__ import annotations

import hashlib
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

MODE = "safe-auto-proposal-thresholds-v1"
BEHAVIOR = "evidence-only"
MIN_CONFIDENCE = 0.95
MIN_TOP_TWO_GAP = 20
FORBIDDEN_REASON_CODES = {
    "source_archive_surface",
    "source_soul_surface",
    "target_soul_surface",
    "canonical_or_global_surface",
    "protected_or_archive_target",
    "backup_shadow_target",
    "archive_shadow_target",
    "trash_shadow_target",
    "duplicate_shadow_target",
    "redirect_shadow_target",
    "canonical_shadow_target",
    "candidate_missing_from_index",
    "operator_review_required",
    "unsafe_candidate_hard_stop",
}
FORBIDDEN_SAFETY_FLAGS = {
    "operator_review_required",
    "hard_stop_candidate_present",
    "archive_or_shadow_target_hard_stop",
    "source_archive_surface",
    "soul_policy_sensitive",
    "ambiguous_link_requires_review",
}


def build_safe_auto_proposal_thresholds_packet(
    candidate_scorer_packet: Mapping[str, Any],
    *,
    packet_id: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    scored_links = list(candidate_scorer_packet.get("scored_links") or candidate_scorer_packet.get("candidate_packets") or [])
    proposals: list[dict[str, Any]] = []
    held: list[dict[str, Any]] = []
    for item in scored_links:
        if not isinstance(item, Mapping):
            continue
        decision = evaluate_candidate_packet_for_auto_proposal(item)
        if decision["eligible"]:
            proposals.append(build_dry_run_proposal(item, decision))
        else:
            held.append({
                "source": str(item.get("source") or ""),
                "old_link": item.get("old_link"),
                "route_hint": str(item.get("route_hint") or ""),
                "reason_codes": decision["reason_codes"],
                "policy_tag": decision["policy_tag"],
            })
    return {
        "schema": MODE,
        "mode": "repo-only/evidence-only",
        "status": "ok",
        "packet_id": packet_id or f"safe-auto-proposal-thresholds-v1-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}",
        "created_at": created_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_candidate_scorer_packet": candidate_scorer_packet.get("packet_id"),
        "behavior": BEHAVIOR,
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "targets": [],
        "apply_authority": "none",
        "thresholds": {
            "min_confidence": MIN_CONFIDENCE,
            "min_top_two_gap": MIN_TOP_TWO_GAP,
            "required_route_hint": "auto-propose",
        },
        "reason_codes": _packet_reason_codes(proposals, held),
        "safety_flags": ["approval_manifest_creation_forbidden", "evidence_only", "no_live_apply"],
        "summary": {
            "source_scored_links": len(scored_links),
            "dry_run_proposals": len(proposals),
            "held_for_review": len(held),
            "policy_tags": dict(sorted(Counter(p["policy_tag"] for p in proposals).items())),
        },
        "dry_run_proposals": sorted(proposals, key=lambda p: (p["file"], p["old_link"], p["proposed_link"])),
        "held_for_review": sorted(held, key=lambda p: (p["source"], str(p.get("old_link") or ""))),
    }


def evaluate_candidate_packet_for_auto_proposal(packet: Mapping[str, Any]) -> dict[str, Any]:
    reasons = set(str(code) for code in packet.get("reason_codes") or [])
    safety_flags = set(str(flag) for flag in packet.get("safety_flags") or [])
    candidates = [c for c in packet.get("candidates") or [] if isinstance(c, Mapping)]
    top = candidates[0] if candidates else {}
    top_reasons = set(str(code) for code in top.get("reason_codes") or [])
    top_flags = set(str(flag) for flag in top.get("safety_flags") or [])
    top_confidence = float(top.get("confidence") or 0.0)
    top_two_gap = int(packet.get("top_two_gap") or 0)
    route = str(packet.get("route_hint") or "")
    failures: list[str] = []
    if route != "auto-propose":
        failures.append("route_not_auto_propose")
    if bool(packet.get("review_required")):
        failures.append("review_required")
    if bool(packet.get("hard_stop")):
        failures.append("hard_stop")
    if len(candidates) != 1:
        failures.append("not_single_candidate")
    if top_confidence < MIN_CONFIDENCE:
        failures.append("confidence_below_threshold")
    if top_two_gap < MIN_TOP_TWO_GAP:
        failures.append("top_two_gap_below_threshold")
    forbidden = sorted((reasons | safety_flags | top_reasons | top_flags) & (FORBIDDEN_REASON_CODES | FORBIDDEN_SAFETY_FLAGS))
    failures.extend(forbidden)
    return {
        "eligible": not failures,
        "reason_codes": failures or ["deterministic_high_confidence_auto_proposal"],
        "policy_tag": "dry-run-auto-propose" if not failures else "hold-for-human-review",
    }


def build_dry_run_proposal(packet: Mapping[str, Any], decision: Mapping[str, Any] | None = None) -> dict[str, Any]:
    candidates = [c for c in packet.get("candidates") or [] if isinstance(c, Mapping)]
    top = candidates[0]
    file_path = str(packet.get("source") or "")
    old_link = str(packet.get("old_link") or packet.get("target_hint") or "")
    proposed_link = str(top.get("path") or "")
    position = _position_from_packet(packet)
    confidence = float(top.get("confidence") or 0.0)
    reason_codes = list((decision or {}).get("reason_codes") or ["deterministic_high_confidence_auto_proposal"])
    rollback_key = _rollback_key(file_path, position, old_link, proposed_link)
    return {
        "file": file_path,
        "position": position,
        "old_link": old_link,
        "proposed_link": proposed_link,
        "confidence": confidence,
        "top_two_gap": int(packet.get("top_two_gap") or 0),
        "reason": ",".join(reason_codes),
        "reason_codes": reason_codes,
        "policy_tag": str((decision or {}).get("policy_tag") or "dry-run-auto-propose"),
        "rollback_key": rollback_key,
        "behavior": BEHAVIOR,
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "targets": [],
        "apply_authority": "none",
    }


def safe_auto_proposal_thresholds_to_markdown(packet: Mapping[str, Any]) -> str:
    summary = packet["summary"]
    lines = [
        "# Safe Auto Proposal Thresholds v1",
        "",
        "Status: evidence-only dry-run proposal generator",
        f"Packet id: `{packet['packet_id']}`",
        f"Created at: `{packet['created_at']}`",
        "",
        "## Safety",
        "",
        f"- behavior: `{packet['behavior']}`",
        f"- live_mutation_authorized: `{str(packet['live_mutation_authorized']).lower()}`",
        f"- approval_manifest_created: `{str(packet['approval_manifest_created']).lower()}`",
        f"- approval_manifest_authority: `{str(packet['approval_manifest_authority']).lower()}`",
        "- targets: `[]`",
        "- apply_authority: `none`",
        "",
        "## Summary",
        "",
        f"- source_scored_links: `{summary['source_scored_links']}`",
        f"- dry_run_proposals: `{summary['dry_run_proposals']}`",
        f"- held_for_review: `{summary['held_for_review']}`",
        "",
        "## Thresholds",
        "",
        f"- min_confidence: `{packet['thresholds']['min_confidence']}`",
        f"- min_top_two_gap: `{packet['thresholds']['min_top_two_gap']}`",
        f"- required_route_hint: `{packet['thresholds']['required_route_hint']}`",
        "",
        "## Boundary",
        "",
        (
            "This packet emits dry-run proposals only. It does not create approval manifests, "
            "live targets, apply authority, or live vault mutations."
        ),
        (
            "Soul, archive, backup, duplicate, redirect, canonical, missing, ambiguous, "
            "hard-stop, and review-required candidates stay held for human review."
        ),
        "",
    ]
    return "\n".join(lines)


def write_safe_auto_proposal_thresholds_packet(
    *,
    candidate_scorer_json: str | Path,
    out_dir: str | Path,
    packet_id: str | None = None,
) -> dict[str, str]:
    source = json.loads(Path(candidate_scorer_json).read_text(encoding="utf-8"))
    packet = build_safe_auto_proposal_thresholds_packet(source, packet_id=packet_id)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    packet_path = out / "safe-auto-proposal-thresholds-v1.json"
    proposals_path = out / "dry-run-proposals.jsonl"
    report_path = out / "REPORT.md"
    packet_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    proposals_path.write_text("".join(json.dumps(p, sort_keys=True) + "\n" for p in packet["dry_run_proposals"]), encoding="utf-8")
    report_path.write_text(safe_auto_proposal_thresholds_to_markdown(packet), encoding="utf-8")
    return {"status": "ok", "packet": str(packet_path), "proposals_jsonl": str(proposals_path), "report": str(report_path)}


def _position_from_packet(packet: Mapping[str, Any]) -> dict[str, Any]:
    for key in ("position", "source_position"):
        value = packet.get(key)
        if isinstance(value, Mapping):
            return dict(value)
    return {
        "line": packet.get("line") or packet.get("source_line"),
        "column": packet.get("column") or packet.get("source_column"),
    }


def _rollback_key(file_path: str, position: Mapping[str, Any], old_link: str, proposed_link: str) -> str:
    payload = json.dumps(
        {"file": file_path, "position": dict(position), "old_link": old_link, "proposed_link": proposed_link},
        sort_keys=True,
    )
    return "rollback:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _packet_reason_codes(proposals: Iterable[Mapping[str, Any]], held: Iterable[Mapping[str, Any]]) -> list[str]:
    codes = {"safe_auto_proposal_thresholds_evidence_only"}
    if list(proposals):
        codes.add("dry_run_proposals_emitted")
    if list(held):
        codes.add("unsafe_or_uncertain_candidates_held")
    return sorted(codes)
