from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

MODE = "proposal-routing-contract-v1"

ROUTE_SUGGEST = "suggest"
ROUTE_AUTO_PROPOSE = "auto-propose"
ROUTE_NEEDS_HUMAN_REVIEW = "needs-human-review"
ROUTE_BLOCKED_REFUSE = "blocked/refuse"

DEFAULT_MIN_CONFIDENCE = 0.95
DEFAULT_MIN_TOP_TWO_GAP = 20

BLOCK_REASON_CODES = {
    "archive_shadow_target",
    "backup_shadow_target",
    "canonical_shadow_target",
    "duplicate_shadow_target",
    "protected_or_archive_target",
    "redirect_shadow_target",
    "source_archive_surface",
    "trash_shadow_target",
    "unsafe_candidate_hard_stop",
}

REVIEW_REASON_CODES = {
    "ambiguous_candidates",
    "candidate_missing_from_index",
    "operator_review_required",
}

PROTECTED_PREFIXES = (
    ".obsidian/",
    ".trash/",
    "_Archive/",
    "_Backups/",
)


@dataclass(frozen=True)
class ProposalRoutingDecision:
    mode: str
    status: str
    route: str
    behavior: str
    reason_codes: list[str]
    safety_flags: list[str]
    ledger_prior: dict[str, Any]
    targets: list[Any]
    dry_run_only: bool
    live_mutation_authorized: bool
    approval_manifest_created: bool
    approval_manifest_authority: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def route_proposal_candidate(
    candidate: Mapping[str, Any],
    *,
    operator_decision_records: Iterable[Mapping[str, Any]] | None = None,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    min_top_two_gap: int = DEFAULT_MIN_TOP_TWO_GAP,
) -> ProposalRoutingDecision:
    """Classify a proposal candidate without granting apply authority."""

    normalized = _normalize_candidate(candidate)
    ledger_prior = _ledger_weak_prior(operator_decision_records or [])
    reason_codes = set(normalized["reason_codes"])
    safety_flags = set(normalized["safety_flags"])
    safety_flags.add("no_live_apply")
    safety_flags.add("no_approval_manifest_authority")
    safety_flags.add("dry_run_only")

    target = normalized["target"]
    if _is_protected_target(target):
        reason_codes.add("protected_or_archive_target")
        safety_flags.add("protected_target_refused")

    if ledger_prior["record_count"]:
        reason_codes.add("operator_decision_ledger_weak_prior")
        safety_flags.add("ledger_prior_not_authoritative")

    if normalized["attempted_authority"]:
        reason_codes.add("attempted_live_apply_or_approval_authority")
        safety_flags.add("attempted_authority_refused")

    block_reasons = reason_codes.intersection(BLOCK_REASON_CODES)
    review_reasons = reason_codes.intersection(REVIEW_REASON_CODES)

    if normalized["hard_stop"] or block_reasons or normalized["attempted_authority"]:
        route = ROUTE_BLOCKED_REFUSE
        reason_codes.add("routing_contract_refused")
    elif normalized["requires_review"] or review_reasons:
        route = ROUTE_NEEDS_HUMAN_REVIEW
        reason_codes.add("routing_contract_human_review_required")
    elif (
        normalized["confidence"] >= min_confidence
        and normalized["top_two_gap"] >= min_top_two_gap
    ):
        route = ROUTE_AUTO_PROPOSE
        reason_codes.add("routing_contract_auto_propose_threshold_met")
    else:
        route = ROUTE_SUGGEST
        reason_codes.add("routing_contract_suggest_only")

    return ProposalRoutingDecision(
        mode=MODE,
        status="ok",
        route=route,
        behavior="routing-only",
        reason_codes=sorted(reason_codes),
        safety_flags=sorted(safety_flags),
        ledger_prior=ledger_prior,
        targets=[],
        dry_run_only=True,
        live_mutation_authorized=False,
        approval_manifest_created=False,
        approval_manifest_authority=False,
    )


def _normalize_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    candidates = candidate.get("candidates") or []
    top = candidates[0] if candidates and isinstance(candidates[0], Mapping) else {}
    return {
        "target": str(
            top.get("path")
            or candidate.get("proposed_target")
            or candidate.get("target")
            or ""
        ),
        "confidence": float(top.get("confidence", candidate.get("confidence", 0.0))),
        "top_two_gap": int(candidate.get("top_two_gap", top.get("top_two_gap", 0))),
        "hard_stop": bool(candidate.get("hard_stop", top.get("hard_stop", False))),
        "requires_review": bool(
            candidate.get("requires_review", candidate.get("review_required", False))
        ),
        "attempted_authority": _attempted_authority(candidate, top),
        "reason_codes": _strings(candidate.get("reason_codes", []))
        + _strings(top.get("reason_codes", [])),
        "safety_flags": _strings(candidate.get("safety_flags", []))
        + _strings(top.get("safety_flags", [])),
    }


def _ledger_weak_prior(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    decision_ids = sorted(
        str(record.get("decision_id") or record.get("id") or "")
        for record in records
        if isinstance(record, Mapping) and (record.get("decision_id") or record.get("id"))
    )
    return {
        "authority": False,
        "behavior": "weak-prior-only",
        "decision_ids": decision_ids,
        "record_count": len(decision_ids),
    }


def _is_protected_target(target: str) -> bool:
    lowered = target.casefold()
    return lowered.startswith(tuple(prefix.casefold() for prefix in PROTECTED_PREFIXES))


def _attempted_authority(candidate: Mapping[str, Any], top: Mapping[str, Any]) -> bool:
    return any(
        bool(record.get(field))
        for record in (candidate, top)
        for field in (
            "live_mutation_authorized",
            "approval_manifest_created",
            "approval_manifest_authority",
        )
    )


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if not isinstance(value, Iterable):
        return []
    return [str(item) for item in value if str(item)]
