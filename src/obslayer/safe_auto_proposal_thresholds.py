from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

MODE = "safe-auto-proposal-thresholds-v1"
POLICY_TAG = "dry-run-safe-auto-proposal-thresholds"
DETERMINISTIC_HIGH_CONFIDENCE = 0.95
DEFAULT_MIN_TOP_TWO_GAP = 20

HARD_STOP_REASON_CODES = {
    "archive_shadow_target",
    "backup_shadow_target",
    "canonical_shadow_target",
    "candidate_missing_from_index",
    "duplicate_shadow_target",
    "protected_or_archive_target",
    "redirect_shadow_target",
    "source_archive_surface",
    "trash_shadow_target",
    "unsafe_candidate_hard_stop",
}
SENSITIVE_TERMS = {
    ".obsidian",
    ".trash",
    "_archive",
    "_backups",
    "archive",
    "backup",
    "canonical",
    "delete",
    "duplicate",
    "global",
    "merge",
    "redirect",
    "rename",
    "soul",
    "trash",
}


@dataclass(frozen=True)
class SafeAutoProposalBundle:
    mode: str
    status: str
    bundle_id: str
    created_at: str
    behavior: str
    live_mutation_authorized: bool
    approval_manifest_created: bool
    approval_manifest_authority: bool
    dry_run_only: bool
    policy_tag: str
    thresholds: dict[str, Any]
    targets: list[Any]
    reason_codes: list[str]
    safety_flags: list[str]
    proposal_items: list[dict[str, Any]]
    exclusions: list[dict[str, Any]]
    operator_decision_ledger_prior: dict[str, Any]
    predicted_metric_delta: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_safe_auto_proposal_bundle(
    scored_packets: Iterable[Mapping[str, Any]],
    *,
    bundle_id: str | None = None,
    created_at: str | None = None,
    min_confidence: float = DETERMINISTIC_HIGH_CONFIDENCE,
    min_top_two_gap: int = DEFAULT_MIN_TOP_TWO_GAP,
    operator_decision_records: Iterable[Mapping[str, Any]] | None = None,
) -> SafeAutoProposalBundle:
    proposal_items: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []

    for index, packet in enumerate(scored_packets):
        normalized = _normalize_mapping(packet)
        item, excluded = _proposal_item_or_exclusion(
            normalized,
            sequence=index,
            min_confidence=min_confidence,
            min_top_two_gap=min_top_two_gap,
        )
        if item is not None:
            proposal_items.append(item)
        if excluded is not None:
            exclusions.append(excluded)

    proposal_items.sort(key=lambda item: (str(item["source_path"]), str(item["proposed_target"])))
    exclusions.sort(key=lambda item: (str(item["source_path"]), str(item.get("proposed_target", ""))))
    found_reasons = {
        code
        for item in proposal_items + exclusions
        for code in item.get("reason_codes", [])
        if isinstance(code, str)
    }
    found_reasons.update({"safe_auto_proposal_thresholds_evidence_only", "no_live_apply_authorized"})

    return SafeAutoProposalBundle(
        mode=MODE,
        status="ok",
        bundle_id=bundle_id or f"safe-auto-proposal-thresholds-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}",
        created_at=created_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        behavior="evidence-only",
        live_mutation_authorized=False,
        approval_manifest_created=False,
        approval_manifest_authority=False,
        dry_run_only=True,
        policy_tag=POLICY_TAG,
        thresholds={"min_confidence": min_confidence, "min_top_two_gap": min_top_two_gap},
        targets=[],
        reason_codes=sorted(found_reasons),
        safety_flags=[
            "approval_manifest_creation_forbidden",
            "evidence_only",
            "ledger_prior_is_weak_evidence_only",
            "no_live_apply",
            "zero_live_writes",
        ],
        proposal_items=proposal_items,
        exclusions=exclusions,
        operator_decision_ledger_prior=_ledger_prior_summary(operator_decision_records or []),
        predicted_metric_delta=_metric_delta(len(proposal_items)),
    )


def serialize_safe_auto_proposal_bundle(bundle: SafeAutoProposalBundle | Mapping[str, Any]) -> str:
    data = bundle.to_dict() if isinstance(bundle, SafeAutoProposalBundle) else _normalize_mapping(bundle)
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def safe_auto_proposal_bundle_to_markdown(bundle: SafeAutoProposalBundle | Mapping[str, Any]) -> str:
    data = bundle.to_dict() if isinstance(bundle, SafeAutoProposalBundle) else _normalize_mapping(bundle)
    lines = [
        "# Safe auto proposal thresholds",
        "",
        f"Bundle id: `{data['bundle_id']}`",
        f"Status: `{data['status']}`",
        "",
        "## Safety",
        "",
        f"- live_mutation_authorized: `{data['live_mutation_authorized']}`",
        f"- approval_manifest_created: `{data['approval_manifest_created']}`",
        f"- approval_manifest_authority: `{data['approval_manifest_authority']}`",
        f"- dry_run_only: `{data['dry_run_only']}`",
        f"- targets: `{len(data['targets'])}`",
        "",
        "## Summary",
        "",
        f"- proposal_items: `{len(data['proposal_items'])}`",
        f"- exclusions: `{len(data['exclusions'])}`",
        f"- policy_tag: `{data['policy_tag']}`",
        "",
    ]
    return "\n".join(lines)


def write_safe_auto_proposal_bundle(
    scored_packets: Iterable[Mapping[str, Any]],
    *,
    out_dir: str | Path,
    bundle_id: str | None = None,
    operator_decision_records: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, str]:
    bundle = build_safe_auto_proposal_bundle(
        scored_packets,
        bundle_id=bundle_id,
        operator_decision_records=operator_decision_records,
    )
    path = Path(out_dir)
    path.mkdir(parents=True, exist_ok=True)
    json_path = path / "proposal-bundle.json"
    markdown_path = path / "proposal-bundle.md"
    json_path.write_text(serialize_safe_auto_proposal_bundle(bundle), encoding="utf-8")
    markdown_path.write_text(safe_auto_proposal_bundle_to_markdown(bundle), encoding="utf-8")
    return {"status": "ok", "bundle": str(json_path), "report": str(markdown_path)}


def _proposal_item_or_exclusion(
    packet: dict[str, Any],
    *,
    sequence: int,
    min_confidence: float,
    min_top_two_gap: int,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    source = str(packet.get("source") or packet.get("source_path") or "")
    candidates = [candidate for candidate in packet.get("candidates", []) if isinstance(candidate, Mapping)]
    top = _normalize_mapping(candidates[0]) if candidates else {}
    target = str(top.get("path") or packet.get("proposed_target") or "")
    confidence = float(top.get("confidence") or packet.get("confidence") or 0.0)
    top_two_gap = int(packet.get("top_two_gap") or 0)
    reason_codes = sorted(
        {
            str(code)
            for code in [*packet.get("reason_codes", []), *top.get("reason_codes", [])]
            if str(code).strip()
        }
    )
    old_link = packet.get("old_link", packet.get("old_text", packet.get("text")))
    exclusion_reasons = _exclusion_reasons(
        packet=packet,
        top=top,
        source=source,
        target=target,
        confidence=confidence,
        top_two_gap=top_two_gap,
        reason_codes=reason_codes,
        min_confidence=min_confidence,
        min_top_two_gap=min_top_two_gap,
    )
    base = {
        "source_file": source,
        "source_path": source,
        "position": packet.get("position", packet.get("line", packet.get("line_number"))),
        "old_link": old_link,
        "old_link_text": old_link,
        "proposed_target": target,
        "proposed_link": _proposed_link(target),
        "confidence": confidence,
        "score": top.get("score", packet.get("score")),
        "top_two_gap": top_two_gap,
        "reason_codes": reason_codes,
        "policy_tag": POLICY_TAG,
        "rollback_key": _rollback_key(source, old_link, target, sequence),
        "predicted_metric_delta": _metric_delta(1),
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
    }
    if exclusion_reasons:
        excluded = dict(base)
        excluded["exclusion_reasons"] = exclusion_reasons
        return None, excluded
    item = dict(base)
    item["proposal_kind"] = "evidence-only-link-target-candidate"
    return item, None


def _exclusion_reasons(
    *,
    packet: dict[str, Any],
    top: dict[str, Any],
    source: str,
    target: str,
    confidence: float,
    top_two_gap: int,
    reason_codes: list[str],
    min_confidence: float,
    min_top_two_gap: int,
) -> list[str]:
    reasons: set[str] = set()
    if not source or not target:
        reasons.add("missing_source_or_target")
    if bool(packet.get("live_mutation_authorized")) or bool(top.get("live_mutation_authorized")):
        reasons.add("input_attempted_live_mutation_authority")
    if bool(packet.get("approval_manifest_created")) or bool(top.get("approval_manifest_created")):
        reasons.add("input_attempted_approval_manifest_authority")
    if bool(packet.get("review_required")) or bool(packet.get("hard_stop")) or bool(top.get("review_required")):
        reasons.add("review_or_hard_stop_required")
    if confidence < min_confidence:
        reasons.add("below_deterministic_high_confidence")
    if top_two_gap < min_top_two_gap:
        reasons.add("insufficient_top_two_gap")
    if HARD_STOP_REASON_CODES.intersection(reason_codes):
        reasons.add("protected_or_archive_collision")
    if _has_sensitive_surface(source) or _has_sensitive_surface(target) or _has_sensitive_reason_code(reason_codes):
        reasons.add("sensitive_surface_or_action")
    return sorted(reasons)


def _has_sensitive_surface(value: str) -> bool:
    normalized = value.casefold()
    parts = {part for part in normalized.replace("\\", "/").replace("-", "/").replace("_", "/").split("/") if part}
    if SENSITIVE_TERMS.intersection(parts) or any(term in normalized for term in (".obsidian", ".trash")):
        return True
    return any(re.search(rf"(^|[^a-z0-9]){re.escape(term)}([^a-z0-9]|$)", normalized) for term in SENSITIVE_TERMS)


def _has_sensitive_reason_code(reason_codes: list[str]) -> bool:
    joined = " ".join(code.casefold() for code in reason_codes)
    return any(term in joined for term in ("archive", "backup", "canonical", "duplicate", "redirect", "trash", "soul"))


def _proposed_link(target: str) -> str:
    if not target:
        return ""
    text = target.removesuffix(".md")
    return f"[[{text}]]"


def _rollback_key(source: str, old_link: Any, target: str, sequence: int) -> str:
    payload = json.dumps(
        {"source": source, "old_link": old_link, "target": target, "sequence": sequence},
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"rollback:{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


def _metric_delta(item_count: int) -> dict[str, Any]:
    return {
        "broken_or_ambiguous_links": -item_count,
        "proposed_link_fixes": item_count,
        "placeholder": True,
    }


def _ledger_prior_summary(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    normalized = [_normalize_mapping(record) for record in records]
    return {
        "behavior": "weak-evidence-only",
        "authority": False,
        "record_count": len(normalized),
        "decision_ids": sorted(str(record.get("decision_id", "")) for record in normalized if record.get("decision_id")),
    }


def _normalize_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): _normalize_jsonable(value[key]) for key in sorted(value, key=str)}


def _normalize_jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _normalize_mapping(value)
    if isinstance(value, set):
        return sorted((_normalize_jsonable(item) for item in value), key=str)
    if isinstance(value, (list, tuple)):
        return [_normalize_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)
