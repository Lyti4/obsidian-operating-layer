from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

from obslayer.external_autograph_policy import external_policy_source, load_external_autograph_policy
from obslayer.guardrails import GuardrailError, load_json, write_json

MODE = "obslayer.manual-review-selector.v1"
POLICY_TAG = "manual-review-only"
EXTERNAL_AUTOGRAPH_POLICY = load_external_autograph_policy()
EXTERNAL_AUTOGRAPH_POLICY_ID = str(EXTERNAL_AUTOGRAPH_POLICY["policy_id"])
EXTERNAL_AUTOGRAPH_POLICY_REF = str(EXTERNAL_AUTOGRAPH_POLICY["policy_ref"])
EXTERNAL_AUTOGRAPH_SOURCE_REPOS = tuple(str(repo) for repo in EXTERNAL_AUTOGRAPH_POLICY["source_repos"])

FORBIDDEN_PATH_PREFIXES = tuple(str(prefix) for prefix in EXTERNAL_AUTOGRAPH_POLICY["protected_path_denylist"])
FORBIDDEN_REASON_CODES = {str(code) for code in EXTERNAL_AUTOGRAPH_POLICY["forbidden_reason_codes"]}
FORBIDDEN_SAFETY_FLAGS = {str(flag) for flag in EXTERNAL_AUTOGRAPH_POLICY["forbidden_safety_flags"]}
SALVAGEABLE_REVIEW_ONLY_ROUTE_HINTS = {str(hint) for hint in EXTERNAL_AUTOGRAPH_POLICY["salvage"]["review_only_route_hints"]}
SALVAGE_REQUIRED_REASON_CODES = {str(code) for code in EXTERNAL_AUTOGRAPH_POLICY["salvage"]["required_reason_codes"]}
SALVAGE_MIN_TOP_TWO_GAP = int(EXTERNAL_AUTOGRAPH_POLICY["salvage"]["min_top_two_gap"])
SALVAGE_MIN_SCORE = int(EXTERNAL_AUTOGRAPH_POLICY["salvage"]["min_score"])
SALVAGE_BATCH_SIZE = int(EXTERNAL_AUTOGRAPH_POLICY["salvage"]["batch_size"])
SALVAGE_INITIAL_SAMPLE_SIZE = int(EXTERNAL_AUTOGRAPH_POLICY["salvage"]["initial_sample_size"])

DATE_TOKEN_RE = re.compile(r"(?:19|20)\d{2}(?:[-_]?\d{2}){0,2}|\d{8}T?\d{0,6}Z?", re.IGNORECASE)
GENERATED_REPORT_PATH_PARTS = tuple(str(part) for part in EXTERNAL_AUTOGRAPH_POLICY["generated_report_noise"]["path_parts"])
GENERATED_REPORT_NOISE_WORDS = tuple(str(word) for word in EXTERNAL_AUTOGRAPH_POLICY["generated_report_noise"]["noise_words"])
PROTECTED_LINK_PARTS = tuple(str(part) for part in EXTERNAL_AUTOGRAPH_POLICY["protected_link_parts"])
DEDUP_ACTION_TAXONOMY = dict(EXTERNAL_AUTOGRAPH_POLICY["dedup_action_taxonomy"])
ALIAS_POLICY_REFS = dict(EXTERNAL_AUTOGRAPH_POLICY["alias_policy_refs"])


def build_manual_review_selector_packet(
    candidate_scorer_packet: Mapping[str, Any],
    *,
    max_candidates: int = 5,
    proposal_packet_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build a repo-only/evidence-only manual review selector packet.

    The selector keeps evidence immutable and emits only read-only review items suitable for
    operator-side triage. It does not grant apply authority.
    """

    if not isinstance(max_candidates, int) or max_candidates < 1:
        raise ValueError("max_candidates must be an integer >= 1")

    packet = dict(candidate_scorer_packet)
    findings: list[str] = []
    findings.extend(_authority_findings(packet))
    if packet.get("status") not in (None, "ok", "ready_for_manual_review", "no_candidate"):
        findings.append("packet status is not a known ready state")

    source_links = dict(
        _load_scored_links_by_key(
            packet,
            source_lookup_roots=_candidate_report_roots(proposal_packet_path),
        )
    )
    has_held_for_review = isinstance(packet.get("held_for_review"), list)
    if has_held_for_review and packet.get("source_candidate_scorer_packet") and not source_links:
        findings.append("source_candidate_scorer_packet could not be resolved to a candidate-scorer packet")

    selection_stats = {
        "route_skip": 0,
        "hard_stop": 0,
        "forbidden_path": Counter(),
        "forbidden_reason_codes": Counter(),
        "forbidden_safety_flags": Counter(),
        "no_candidates": 0,
        "blocked_refuse_salvaged": 0,
        "blocked_refuse_rejected": Counter(),
        "blocked_refuse_hard_reject": Counter(),
        "blocked_refuse_soft_reject": Counter(),
        "rejected_samples": [],
    }

    links = list(_candidate_links(packet, source_lookup=source_links))
    selected: list[dict[str, Any]] = []
    for link in links:
        item = _link_to_review_item(link, selection_stats)
        if item:
            selected.append(item)

    selected.sort(key=_review_item_sort_key, reverse=True)
    selected = _with_review_queue_metadata(selected)
    shortlisted = selected[:max_candidates]

    status = "ready_for_manual_review" if shortlisted and not findings else "no_candidate"
    if findings:
        status = "blocked"

    route_counts = {"needs-human-review": 0, "suggest": 0, "other": 0}
    for item in shortlisted:
        route = item.get("route_hint", "other")
        route_counts[route if route in route_counts else "other"] += 1

    selection_diagnostics = {
        "route_skip": selection_stats["route_skip"],
        "hard_stop": selection_stats["hard_stop"],
        "forbidden_path": {
            "total": sum(selection_stats["forbidden_path"].values()),
            "reasons": dict(selection_stats["forbidden_path"]),
        },
        "forbidden_reason_codes": {
            "total": sum(selection_stats["forbidden_reason_codes"].values()),
            "reasons": dict(selection_stats["forbidden_reason_codes"]),
        },
        "forbidden_safety_flags": {
            "total": sum(selection_stats["forbidden_safety_flags"].values()),
            "flags": dict(selection_stats["forbidden_safety_flags"]),
        },
        "no_candidates": selection_stats["no_candidates"],
        "blocked_refuse_salvaged": selection_stats["blocked_refuse_salvaged"],
        "blocked_refuse_rejected": {
            "total": sum(selection_stats["blocked_refuse_rejected"].values()),
            "reasons": dict(selection_stats["blocked_refuse_rejected"]),
            "hard_reject": dict(selection_stats["blocked_refuse_hard_reject"]),
            "soft_reject": dict(selection_stats["blocked_refuse_soft_reject"]),
        },
        "rejected_samples": selection_stats["rejected_samples"][:10],
        "selected": len(shortlisted),
        "candidate_pool_selected": len(selected),
    }

    return {
        "schema": MODE,
        "mode": "repo-only/evidence-only",
        "packet_type": "manual_review_evidence_only",
        "authority_scope": "review_only",
        "status": status,
        "manual_review_only": True,
        "live_mutation_authorized": False,
        "live_mutation_allowed": False,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "approval_manifest": None,
        "targets": [],
        "apply_authority": "none",
        "requires_explicit_approval_before_apply": True,
        "source_packet_schema": packet.get("schema"),
        "source_packet_id": packet.get("packet_id"),
        "findings": findings,
        "review_items": shortlisted,
        "summary": {
            "source_links_processed": len(links),
            "selected": len(shortlisted),
            "review_items": len(shortlisted),
            "max_candidates": max_candidates,
            "route_hint": route_counts,
            "selection_diagnostics": selection_diagnostics,
            "selection_contract": _selection_contract_summary(),
            "batching": _batching_metadata(
                accepted_total=len(selected),
                shortlisted_total=len(shortlisted),
                rejected_samples_total=len(selection_stats["rejected_samples"]),
            ),
            "no_candidate_causes": _selection_rejection_causes(selection_diagnostics) if status == "no_candidate" else [],
        },
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }


def _candidate_links(
    packet: Mapping[str, Any],
    source_lookup: Mapping[tuple[str, str], Mapping[str, Any]] | None = None,
    source_lookup_roots: Iterable[Path] | None = None,
) -> Iterable[Mapping[str, Any]]:
    """Yield candidate links from either candidate-scorer or safe-auto threshold packets."""
    raw_scored = packet.get("scored_links") or packet.get("candidate_packets")
    if isinstance(raw_scored, list):
        for item in raw_scored:
            if isinstance(item, Mapping):
                yield item
        return

    held = packet.get("held_for_review")
    if isinstance(held, list):
        source_lookup = source_lookup or _load_scored_links_by_key(
            packet,
            source_lookup_roots=source_lookup_roots,
        )
        for item in held:
            if not isinstance(item, Mapping):
                continue
            combined = _attach_scored_link(item, source_lookup)
            yield combined
        return


def _candidate_report_roots(proposal_packet_path: str | Path | None = None) -> tuple[Path, ...]:
    roots: list[Path] = []

    if proposal_packet_path is not None:
        proposal_dir = Path(proposal_packet_path).expanduser().resolve().parent
        for ancestor in [proposal_dir] + list(proposal_dir.parents):
            if ancestor.name == "candidate-scorer-v1":
                roots.append(ancestor)
                break
            if ancestor.name == "safe-auto-proposal-thresholds-v1":
                roots.append(ancestor.parent / "candidate-scorer-v1")

    package_root = Path(__file__).resolve().parents[2]
    roots.append(package_root / "out" / "reports" / "candidate-scorer-v1")
    roots.append(Path.cwd() / "out" / "reports" / "candidate-scorer-v1")

    existing_unique: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        resolved = root.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        existing_unique.append(resolved)
    return tuple(existing_unique)


def _load_scored_links_by_key(
    packet: Mapping[str, Any],
    source_lookup_roots: Iterable[Path] | None = None,
) -> dict[tuple[str, str], Mapping[str, Any]]:
    path = packet.get("source_candidate_scorer_packet")
    if not isinstance(path, str):
        return {}

    source_path = _resolve_source_candidate_packet_path(
        path,
        source_lookup_roots=source_lookup_roots,
    )
    if source_path is None:
        return {}

    try:
        source_packet = load_json(source_path)
    except (OSError, json.JSONDecodeError, ValueError):
        return {}

    scored = source_packet.get("scored_links")
    if not isinstance(scored, list):
        return {}

    lookup: dict[tuple[str, str], Mapping[str, Any]] = {}
    for item in scored:
        if not isinstance(item, Mapping):
            continue
        source = str(item.get("source") or "")
        old_link = str(item.get("old_link") or item.get("target_hint") or "")
        key = (source.strip(), old_link.strip())
        lookup[key] = item
    return lookup


def _resolve_source_candidate_packet_path(
    raw_path: str,
    source_lookup_roots: Iterable[Path] | None = None,
) -> Path | None:
    candidate_id_or_path = Path(raw_path.strip())
    if candidate_id_or_path.exists():
        return candidate_id_or_path

    fallback_path = Path.cwd() / candidate_id_or_path
    if fallback_path.exists():
        return fallback_path

    target_id = raw_path.strip()
    if not target_id:
        return None

    report_roots = list(source_lookup_roots or _candidate_report_roots())
    if not report_roots:
        return None

    for reports_root in report_roots:
        if not reports_root.exists():
            continue

        by_name = reports_root / f"{target_id}.json"
        if by_name.exists():
            return by_name

        target_variants = [target_id]
        prefix = "candidate-scorer-v1-"
        if target_id.startswith(prefix):
            target_variants.append(target_id.removeprefix(prefix))

        for target_variant in target_variants:
            under_timestamp = reports_root / target_variant / "candidate-scorer-v1.json"
            if under_timestamp.exists():
                return under_timestamp

        for candidate_path in sorted(reports_root.rglob("candidate-scorer-v1.json")):
            try:
                payload = load_json(candidate_path)
            except (OSError, json.JSONDecodeError, ValueError):
                continue
            if str(payload.get("packet_id") or "") == target_id:
                return candidate_path

    return None


def _selection_contract_summary() -> dict[str, Any]:
    return {
        "policy_tag": POLICY_TAG,
        "authority": "manual-review-only",
        "source_policy": _source_policy("manual-review-selector-contract"),
        "classification": "manual_review_only_selector",
        "risk": "medium",
        "apply_authority": "none",
        "protected_path_denylist": list(FORBIDDEN_PATH_PREFIXES),
        "generated_report_noise_denylist": {
            "path_parts": list(GENERATED_REPORT_PATH_PARTS),
            "noise_words": list(GENERATED_REPORT_NOISE_WORDS),
        },
        "link_resolution_classes": {
            "exact_or_unique": {"classification": "link_resolution_safe_candidate", "risk": "low", "apply_authority": "none"},
            "ambiguous_or_missing": {"classification": "link_resolution_manual_only", "risk": "medium", "apply_authority": "none"},
            "protected_or_generated": {"classification": "link_resolution_denied", "risk": "high", "apply_authority": "none"},
        },
        "dedup_action_taxonomy": DEDUP_ACTION_TAXONOMY,
        "manifest_approval_contract": {
            "approved_default": False,
            "approved_false_means_no_apply": True,
            "approved_true_requires_operator_manifest": True,
        },
        "hard_reject_causes": [
            "source_forbidden_surface",
            "top_candidate_hard_stop",
            "top_candidate_forbidden_path",
            "top_candidate_forbidden_safety_flag",
            "top_candidate_forbidden_reason_code",
        ],
        "soft_reject_causes": [
            "top_candidate_not_active_exact",
            "top_candidate_low_score",
            "top_two_gap_too_small",
        ],
        "salvage_thresholds": {
            "min_score": SALVAGE_MIN_SCORE,
            "min_top_two_gap": SALVAGE_MIN_TOP_TWO_GAP,
            "required_reason_codes": sorted(SALVAGE_REQUIRED_REASON_CODES),
            "allowed_top_candidate_safety_flags": ["ambiguous_link_requires_review"],
        },
    }


def _source_policy(rule_id: str) -> dict[str, Any]:
    return external_policy_source(rule_id)


def _link_policy_metadata(
    *,
    route_hint: str,
    reason_codes: Iterable[str],
    safety_flags: Iterable[str],
    salvage_mode: bool,
) -> dict[str, Any]:
    normalized_reason_codes = {str(code) for code in reason_codes}
    normalized_flags = {str(flag) for flag in safety_flags}

    if salvage_mode:
        classification = "blocked_refuse_salvage_manual_review"
        risk = "medium"
        rule_id = "link-resolution-blocked-refuse-salvage"
    elif "ambiguous_link_requires_review" in normalized_flags or "ambiguous" in route_hint:
        classification = "link_resolution_manual_only"
        risk = "medium"
        rule_id = "link-resolution-ambiguous-manual"
    elif {"active_target_available", "exact_title_match"}.issubset(normalized_reason_codes) or (
        "exact_path_match" in normalized_reason_codes
    ):
        classification = "link_resolution_safe_candidate"
        risk = "low"
        rule_id = "link-resolution-exact-or-unique"
    else:
        classification = "link_resolution_manual_only"
        risk = "medium"
        rule_id = "link-resolution-manual-review"

    return {
        "source_policy": _source_policy(rule_id),
        "classification": classification,
        "risk": risk,
        "apply_authority": "none",
    }


def _batching_metadata(*, accepted_total: int, shortlisted_total: int, rejected_samples_total: int) -> dict[str, Any]:
    batches = []
    for start in range(0, accepted_total, SALVAGE_BATCH_SIZE):
        end = min(start + SALVAGE_BATCH_SIZE, accepted_total)
        batches.append(
            {
                "batch_index": len(batches) + 1,
                "start_index": start,
                "end_index_exclusive": end,
                "size": end - start,
                "review_mode": "manual-review-only",
            }
        )
    return {
        "accepted_total": accepted_total,
        "shortlisted_total": shortlisted_total,
        "recommended_initial_sample_size": min(SALVAGE_INITIAL_SAMPLE_SIZE, accepted_total),
        "recommended_batch_size": SALVAGE_BATCH_SIZE,
        "batches": batches,
        "include_rejected_samples_in_initial_review": rejected_samples_total > 0,
        "rejected_samples_total": rejected_samples_total,
    }


def _selection_rejection_causes(selection_diagnostics: Mapping[str, Any]) -> list[str]:
    causes: list[str] = []
    route_skip = int(selection_diagnostics.get("route_skip", 0) or 0)
    hard_stop = int(selection_diagnostics.get("hard_stop", 0) or 0)
    no_candidates = int(selection_diagnostics.get("no_candidates", 0) or 0)
    forbidden_path = selection_diagnostics.get("forbidden_path", {})
    forbidden_reasons = selection_diagnostics.get("forbidden_reason_codes", {})
    forbidden_flags = selection_diagnostics.get("forbidden_safety_flags", {})
    blocked_refuse_rejected = selection_diagnostics.get("blocked_refuse_rejected", {})

    if route_skip:
        causes.append("route_skip")
    if hard_stop:
        causes.append("hard_stop")
    if no_candidates:
        causes.append("no_candidates")
    if int(forbidden_path.get("total", 0) or 0):
        causes.append("forbidden_path")
    if int(forbidden_reasons.get("total", 0) or 0):
        causes.append("forbidden_reason_code")
    if int(forbidden_flags.get("total", 0) or 0):
        causes.append("forbidden_safety_flag")
    if int(blocked_refuse_rejected.get("total", 0) or 0):
        causes.append("blocked_refuse_rejected")

    if not causes:
        causes.append("no_review_candidates")
    return causes


def _attach_scored_link(
    item: Mapping[str, Any],
    lookup: Mapping[tuple[str, str], Mapping[str, Any]],
) -> Mapping[str, Any]:
    source = str(item.get("source") or "")
    old_link = str(item.get("old_link") or "")
    key = (source.strip(), old_link.strip())
    source_item = lookup.get(key)
    if source_item is None:
        return item
    merged = dict(item)
    merged["candidates"] = source_item.get("candidates")
    merged["top_two_gap"] = source_item.get("top_two_gap")
    merged["route_hint"] = str(item.get("route_hint") or source_item.get("route_hint") or "")
    merged["reason_codes"] = list(_as_codes(item.get("reason_codes"), source_item.get("reason_codes")))
    merged["safety_flags"] = list(_as_codes(item.get("safety_flags"), source_item.get("safety_flags")))
    return merged


def _increment_counter(counter: Counter[str], key: str) -> None:
    if key:
        counter[key] += 1


def _link_to_review_item(
    link: Mapping[str, Any],
    selection_stats: Mapping[str, Any],
) -> dict[str, Any] | None:
    route_hint = str(link.get("route_hint") or "")
    salvage_mode = route_hint in SALVAGEABLE_REVIEW_ONLY_ROUTE_HINTS
    if not _is_route_for_manual_review(link) and not salvage_mode:
        if isinstance(selection_stats, dict):
            selection_stats["route_skip"] += 1
        return None
    if bool(link.get("hard_stop")) and not salvage_mode:
        if isinstance(selection_stats, dict):
            selection_stats["hard_stop"] += 1
        return None

    candidates = [c for c in link.get("candidates") or [] if isinstance(c, Mapping)]
    if not candidates:
        if isinstance(selection_stats, dict):
            selection_stats["no_candidates"] += 1
        return None

    top = candidates[0]
    if salvage_mode:
        rejection = _blocked_refuse_salvage_rejection(link, top, candidates)
        if rejection:
            if isinstance(selection_stats, dict):
                _record_blocked_refuse_rejection(selection_stats, link, top, rejection)
            return None
        if isinstance(selection_stats, dict):
            selection_stats["blocked_refuse_salvaged"] += 1
    proposed_path = str(top.get("path") or top.get("proposed_path") or "")
    if not proposed_path or _is_forbidden_path(proposed_path):
        if isinstance(selection_stats, dict):
            key = proposed_path.lower() if proposed_path else "<missing-path>"
            if key == "<missing-path>":
                _increment_counter(selection_stats["forbidden_path"], "<missing>")
            else:
                for prefix in FORBIDDEN_PATH_PREFIXES:
                    if Path(proposed_path.replace("\\", "/")).as_posix().lower().startswith(prefix.lower()):
                        _increment_counter(selection_stats["forbidden_path"], prefix)
                        break
                else:
                    _increment_counter(selection_stats["forbidden_path"], "path-filter")
        return None

    link_reason_codes = _as_codes(link.get("reason_codes"))
    candidate_reason_codes = _as_codes(top.get("reason_codes"))
    reason_codes = sorted(set(link_reason_codes) | set(candidate_reason_codes))
    if salvage_mode:
        reason_codes = sorted(set(candidate_reason_codes) | {"blocked_refuse_salvaged_for_manual_review"})
    if _is_forbidden_reason_codes(reason_codes):
        if isinstance(selection_stats, dict):
            for reason in reason_codes:
                if reason in FORBIDDEN_REASON_CODES:
                    _increment_counter(selection_stats["forbidden_reason_codes"], reason)
        return None

    safety_flags = sorted(set(_as_codes(link.get("safety_flags"))) | set(_as_codes(top.get("safety_flags"))))
    if salvage_mode:
        safety_flags = _as_codes(top.get("safety_flags"))
    if _is_forbidden_safety_flags(safety_flags) and not salvage_mode:
        if isinstance(selection_stats, dict):
            for flag in safety_flags:
                if flag in FORBIDDEN_SAFETY_FLAGS:
                    _increment_counter(selection_stats["forbidden_safety_flags"], flag)
        return None

    source = str(link.get("source") or "")
    old_link = str(link.get("old_link") or link.get("target_hint") or "")
    confidence = top.get("confidence")
    if not isinstance(confidence, (int, float)):
        confidence = 0.0
    score = top.get("score")
    if not isinstance(score, (int, float)):
        score = 0
    top_two_gap = int(link.get("top_two_gap") or 0)

    unsafe_lower_ranked = _unsafe_lower_ranked_candidates(candidates)
    review_reason = _build_review_reason(route_hint, reason_codes)
    salvage_reason = None
    if salvage_mode:
        salvage_reason = (
            "top_active_exact_candidate_lower_ranked_shadow_candidates_only"
            if unsafe_lower_ranked
            else "top_active_exact_candidate_single_candidate_manual_review_only"
        )
        review_reason = (
            "blocked/refuse salvage: top active exact candidate retained for manual review; original blocked/refuse provenance preserved"
        )
    policy_metadata = _link_policy_metadata(
        route_hint=route_hint,
        reason_codes=reason_codes,
        safety_flags=safety_flags,
        salvage_mode=salvage_mode,
    )
    review_item = {
        "source": source,
        "old_link": old_link,
        "proposed_path": proposed_path,
        "confidence": float(confidence),
        "score": int(score),
        "top_two_gap": top_two_gap,
        "route_hint": route_hint,
        "reason_codes": reason_codes,
        "review_reason": review_reason,
        "policy_tag": POLICY_TAG,
        "policy_taxonomy": {
            "schema": MODE,
            "packet_type": "manual_review_evidence_only",
            "authority": "manual-review-only",
            "route_class": "salvaged_blocked_refuse" if salvage_mode else "direct_manual_review",
            "decision_class": "soft_salvage_candidate" if salvage_mode else "manual_review_candidate",
            "apply_authority": "none",
            "source_policy": policy_metadata["source_policy"],
            "classification": policy_metadata["classification"],
            "risk": policy_metadata["risk"],
        },
        "source_policy": policy_metadata["source_policy"],
        "classification": policy_metadata["classification"],
        "risk": policy_metadata["risk"],
        "manual_review_only": True,
        "approval_manifest_id": None,
        "apply_authority": "none",
        "live_mutation_authorized": False,
        "proposed_action": "review_only",
        "candidate_count": len(candidates),
        "top_score": int(score),
        "thresholds": {
            "salvage_min_score": SALVAGE_MIN_SCORE,
            "salvage_min_top_two_gap": SALVAGE_MIN_TOP_TWO_GAP,
        },
        "source_provenance": {
            "route_hint": route_hint,
            "hard_stop": bool(link.get("hard_stop")),
            "reason_codes": link_reason_codes,
            "safety_flags": _as_codes(link.get("safety_flags")),
        },
        "top_candidate_path": proposed_path,
        "selection_mode": "blocked_refuse_salvage" if salvage_mode else "direct_manual_review",
        "blocked_refuse_salvage_reason": salvage_reason,
        "unsafe_lower_ranked_candidates_count": len(unsafe_lower_ranked),
        "unsafe_lower_ranked_candidate_reasons": _unsafe_lower_ranked_reason_summary(unsafe_lower_ranked),
        "rank_features": _review_rank_features(
            source=source,
            route_hint=route_hint,
            reason_codes=reason_codes,
            safety_flags=safety_flags,
            confidence=float(confidence),
            score=int(score),
            top_two_gap=top_two_gap,
        ),
    }
    return review_item


def _with_review_queue_metadata(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queued: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        batch_index = (index // SALVAGE_BATCH_SIZE) + 1
        batch_start = (batch_index - 1) * SALVAGE_BATCH_SIZE
        batch_end = min(batch_start + SALVAGE_BATCH_SIZE, len(items))
        queued_item = dict(item)
        queued_item["review_queue"] = {
            "item_id": _review_item_id(item),
            "batch_id": f"manual-review-only-{batch_index:04d}",
            "batch_index": batch_index,
            "item_index": index,
            "item_index_in_batch": index - batch_start,
            "batch_start_index": batch_start,
            "batch_end_index_exclusive": batch_end,
            "batch_size": batch_end - batch_start,
            "recommended_batch_size": SALVAGE_BATCH_SIZE,
            "review_mode": "manual-review-only",
        }
        queued.append(queued_item)
    return queued


def _review_item_id(item: Mapping[str, Any]) -> str:
    stable_key = json.dumps(
        {
            "source": item.get("source", ""),
            "old_link": item.get("old_link", ""),
            "proposed_path": item.get("proposed_path", ""),
            "selection_mode": item.get("selection_mode", ""),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    digest = hashlib.sha256(stable_key.encode("utf-8")).hexdigest()[:16]
    return f"manual-review-only-{digest}"


def _as_codes(*raw_values: Any) -> list[str]:
    merged: list[str] = []
    for raw in raw_values:
        if not raw:
            continue
        if isinstance(raw, str):
            merged.append(raw)
            continue
        if isinstance(raw, Iterable):
            merged.extend(str(item) for item in raw if str(item))
    return sorted(set(merged))


def _is_route_for_manual_review(link: Mapping[str, Any]) -> bool:
    route_hint = str(link.get("route_hint") or "")
    return route_hint in {"needs-human-review", "suggest"}


def _blocked_refuse_salvage_rejection(
    link: Mapping[str, Any],
    top: Mapping[str, Any],
    candidates: list[Mapping[str, Any]],
) -> str | None:
    source = str(link.get("source") or "")
    proposed_path = str(top.get("path") or top.get("proposed_path") or "")
    top_reason_codes = set(_as_codes(top.get("reason_codes")))
    top_flags = set(_as_codes(top.get("safety_flags")))
    top_two_gap = _as_int(link.get("top_two_gap"))
    score = _as_int(top.get("score"))

    if _is_forbidden_source_path(source):
        return "source_forbidden_surface"
    if bool(top.get("hard_stop")):
        return "top_candidate_hard_stop"
    if not proposed_path or _is_forbidden_path(proposed_path):
        return "top_candidate_forbidden_path"
    if not SALVAGE_REQUIRED_REASON_CODES.issubset(top_reason_codes):
        return "top_candidate_not_active_exact"
    if top_flags - {"ambiguous_link_requires_review"}:
        return "top_candidate_forbidden_safety_flag"
    if _is_forbidden_reason_codes(top_reason_codes):
        return "top_candidate_forbidden_reason_code"
    if score < SALVAGE_MIN_SCORE:
        return "top_candidate_low_score"
    if top_two_gap < SALVAGE_MIN_TOP_TWO_GAP:
        return "top_two_gap_too_small"
    return None


def _record_blocked_refuse_rejection(
    selection_stats: dict[str, Any],
    link: Mapping[str, Any],
    top: Mapping[str, Any],
    rejection: str,
) -> None:
    _increment_counter(selection_stats["blocked_refuse_rejected"], rejection)
    category = _blocked_refuse_rejection_category(rejection)
    _increment_counter(selection_stats[f"blocked_refuse_{category}_reject"], rejection)
    samples = selection_stats.get("rejected_samples")
    if isinstance(samples, list) and len(samples) < 10:
        samples.append(
            {
                "reason": rejection,
                "source": str(link.get("source") or ""),
                "old_link": str(link.get("old_link") or link.get("target_hint") or ""),
                "top_candidate_path": str(top.get("path") or top.get("proposed_path") or ""),
                "score": _as_int(top.get("score")),
                "confidence": _as_float(top.get("confidence")),
                "top_two_gap": _as_int(link.get("top_two_gap")),
                "policy_tag": POLICY_TAG,
                "selection_mode": "blocked_refuse_rejected",
                "rejection_category": category,
                "source_reason_codes": _as_codes(link.get("reason_codes")),
                "source_safety_flags": _as_codes(link.get("safety_flags")),
            }
        )


def _blocked_refuse_rejection_category(rejection: str) -> str:
    hard_rejections = {
        "source_forbidden_surface",
        "top_candidate_hard_stop",
        "top_candidate_forbidden_path",
        "top_candidate_forbidden_safety_flag",
        "top_candidate_forbidden_reason_code",
    }
    return "hard" if rejection in hard_rejections else "soft"


def _unsafe_lower_ranked_candidates(candidates: list[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [candidate for candidate in candidates[1:] if bool(candidate.get("hard_stop"))]


def _unsafe_lower_ranked_reason_summary(candidates: list[Mapping[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for candidate in candidates:
        for reason in _as_codes(candidate.get("reason_codes"), candidate.get("safety_flags")):
            if reason in FORBIDDEN_REASON_CODES or reason in FORBIDDEN_SAFETY_FLAGS:
                counter[reason] += 1
    return dict(counter)


def _is_forbidden_reason_codes(reason_codes: Iterable[str]) -> bool:
    normalized = {str(code) for code in reason_codes}
    return bool(normalized & FORBIDDEN_REASON_CODES)


def _is_forbidden_safety_flags(safety_flags: Iterable[str]) -> bool:
    normalized = {str(flag) for flag in safety_flags}
    return bool(normalized & FORBIDDEN_SAFETY_FLAGS)


def _is_forbidden_path(path: str) -> bool:
    normalized = path.strip().replace("\\", "/")
    lower = normalized.lower()
    return (
        any(lower.startswith(prefix.lower()) for prefix in FORBIDDEN_PATH_PREFIXES)
        or "soul/" in lower
        or _is_generated_report_path(path)
    )


def _is_generated_report_path(path: str) -> bool:
    lower = path.strip().replace("\\", "/").lower()
    stem_tokens = {token for token in re.split(r"[^a-z0-9]+", Path(lower).stem) if token}
    return any(part in lower for part in GENERATED_REPORT_PATH_PARTS) or bool(stem_tokens & set(GENERATED_REPORT_NOISE_WORDS))


def _is_forbidden_source_path(path: str) -> bool:
    normalized = path.strip().replace("\\", "/").lower()
    return (
        _is_forbidden_path(path)
        or "/_archive/" in normalized
        or "/_backups/" in normalized
        or "/.trash/" in normalized
        or "/soul/" in normalized
        or "/soul-vault/" in normalized
    )


def _build_review_reason(route_hint: str, reason_codes: Iterable[str]) -> str:
    codes = sorted(str(code) for code in reason_codes)
    if codes:
        return f"route {route_hint}: {', '.join(codes)}"
    return f"route {route_hint}: manual_review_required"


def _review_rank_features(
    *,
    source: str,
    route_hint: str,
    reason_codes: Iterable[str],
    safety_flags: Iterable[str],
    confidence: float,
    score: int,
    top_two_gap: int,
) -> dict[str, int]:
    normalized_reason_codes = {str(code) for code in reason_codes}
    normalized_flags = {str(flag) for flag in safety_flags}

    points = 0
    if route_hint == "needs-human-review":
        points += 120
    elif route_hint == "suggest":
        points += 90
    elif route_hint in SALVAGEABLE_REVIEW_ONLY_ROUTE_HINTS:
        points += 80

    if source.startswith("Memory-Vault/"):
        points += 30
    if "active_target_available" in normalized_reason_codes:
        points += 35
    if "exact_title_match" in normalized_reason_codes:
        points += 25
    if "alias_match" in normalized_reason_codes:
        points += 15

    points += min(100, int(confidence * 100))
    points += min(20, int(score / 5)) if isinstance(score, int) else 0
    points += min(25, min(40, top_two_gap))

    if "ambiguous_link_requires_review" in normalized_flags:
        points -= 20

    return {
        "route_hint_score": _route_hint_rank_points(route_hint),
        "active_memory": 1 if source.startswith("Memory-Vault/") else 0,
        "reason_code_score": (
            (35 if "active_target_available" in normalized_reason_codes else 0)
            + (25 if "exact_title_match" in normalized_reason_codes else 0)
            + (15 if "alias_match" in normalized_reason_codes else 0)
        ),
        "confidence_points": min(100, int(confidence * 100)),
        "score_points": min(20, int(score / 5)) if isinstance(score, int) else 0,
        "top_two_gap_points": min(25, min(40, top_two_gap)),
        "total_points": points,
    }


def _route_hint_rank_points(route_hint: str) -> int:
    if route_hint == "needs-human-review":
        return 120
    if route_hint == "suggest":
        return 90
    if route_hint in SALVAGEABLE_REVIEW_ONLY_ROUTE_HINTS:
        return 80
    return 0


def _review_item_sort_key(item: Mapping[str, Any]) -> tuple[int, float, int]:
    rank = _as_int(item.get("rank_features", {}).get("total_points"))
    confidence = _as_float(item.get("confidence"))
    score = _as_int(item.get("score"))
    return (rank, confidence, score)


def _authority_findings(packet: Mapping[str, Any]) -> list[str]:
    findings = []
    if packet.get("live_mutation_authorized") is not False:
        findings.append("live_mutation_authorized must be false")
    if packet.get("approval_manifest_created") is not False:
        findings.append("approval_manifest_created must be false")
    if packet.get("approval_manifest_authority") not in (None, False):
        findings.append("approval_manifest_authority must be false")
    if packet.get("apply_authority", "none") != "none":
        findings.append("apply_authority must be none")
    if packet.get("targets") not in (None, []):
        findings.append("targets must be empty for selector packet")
    return findings


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def manual_review_selector_to_markdown(packet: Mapping[str, Any]) -> str:
    review_items = packet.get("review_items")
    if not isinstance(review_items, list):
        review_items = []

    lines = [
        "# Manual Review Selector",
        "",
        "Mode: repo-only/evidence-only",
        f"- status: `{packet.get('status')}`",
        f"- packet id: `{packet.get('source_packet_id')}`",
        f"- source schema: `{packet.get('source_packet_schema')}`",
        "",
        "## Safety",
        f"- live_mutation_authorized: `{str(packet.get('live_mutation_authorized')).lower()}`",
        f"- approval_manifest_created: `{str(packet.get('approval_manifest_created')).lower()}`",
        f"- apply_authority: `{packet.get('apply_authority')}`",
        f"- targets: `{packet.get('targets')}`",
        "",
        "## Summary",
        f"- source links processed: `{packet.get('summary', {}).get('source_links_processed')}`",
        f"- selected: `{packet.get('summary', {}).get('selected')}`",
        f"- review items: `{packet.get('summary', {}).get('review_items')}`",
        f"- max candidates: `{packet.get('summary', {}).get('max_candidates')}`",
        f"- route_skip: `{packet.get('summary', {}).get('selection_diagnostics', {}).get('route_skip')}`",
        f"- hard_stop: `{packet.get('summary', {}).get('selection_diagnostics', {}).get('hard_stop')}`",
        f"- forbidden_path: `{packet.get('summary', {}).get('selection_diagnostics', {}).get('forbidden_path', {}).get('total')}`",
        f"- no_candidates: `{packet.get('summary', {}).get('selection_diagnostics', {}).get('no_candidates')}`",
        f"- blocked_refuse_salvaged: `{packet.get('summary', {}).get('selection_diagnostics', {}).get('blocked_refuse_salvaged')}`",
        "- blocked_refuse_rejected: `"
        f"{packet.get('summary', {}).get('selection_diagnostics', {}).get('blocked_refuse_rejected', {}).get('total')}`",
        "",
        "## Review shortlist",
        "",
    ]

    if review_items:
        lines.append("| source | old link | proposed path | confidence | score | route | selection mode | unsafe lower | review reason |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for item in review_items:
            lines.append(
                (
                    "| {source} | {old_link} | {proposed_path} | {confidence} | {score} | "
                    "{route_hint} | {selection_mode} | {unsafe_lower} | {review_reason} |"
                ).format(
                    source=item.get("source", ""),
                    old_link=item.get("old_link", ""),
                    proposed_path=item.get("proposed_path", ""),
                    confidence=f"{item.get('confidence', 0):.3f}",
                    score=item.get("score", 0),
                    route_hint=item.get("route_hint", ""),
                    selection_mode=item.get("selection_mode", ""),
                    unsafe_lower=item.get("unsafe_lower_ranked_candidates_count", 0),
                    review_reason=item.get("review_reason", ""),
                )
            )
    else:
        lines.append("No review items were selected.")
        diagnostics = packet.get("summary", {}).get("selection_diagnostics", {})
        if diagnostics:
            route_skip = diagnostics.get("route_skip", 0)
            hard_stop = diagnostics.get("hard_stop", 0)
            no_candidates = diagnostics.get("no_candidates", 0)
            forbidden_path = diagnostics.get("forbidden_path", {}).get("total", 0)
            reason_codes = diagnostics.get("forbidden_reason_codes", {})
            safety_flags = diagnostics.get("forbidden_safety_flags", {})
            if any(x for x in (route_skip, hard_stop, no_candidates, forbidden_path, reason_codes, safety_flags)):
                reason_lines = [
                    f"route_skip={route_skip}",
                    f"hard_stop={hard_stop}",
                    f"no_candidates={no_candidates}",
                    f"forbidden_path={forbidden_path}",
                ]
                if reason_codes:
                    reason_lines.append(f"forbidden_reason_codes={reason_codes}")
                if safety_flags:
                    reason_lines.append(f"forbidden_safety_flags={safety_flags}")
                lines.append(f"- no candidate reasons: {'; '.join(reason_lines)}")

    lines.extend(["", "## Findings", ""])
    findings = packet.get("findings")
    if findings:
        lines.extend(f"- {finding}" for finding in findings)
    else:
        lines.append("- none")

    return "\n".join(lines)


def write_manual_review_selector_packet(
    *,
    proposal_packet: str | Path,
    out_dir: str | Path,
    max_candidates: int = 5,
) -> dict[str, str]:
    packet = build_manual_review_selector_packet(
        load_json(proposal_packet),
        max_candidates=max_candidates,
        proposal_packet_path=proposal_packet,
    )
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    selector_path = out / "manual-review-selector-v1.json"
    shortlisted_path = out / "manual-review-items.jsonl"
    report_path = out / "REPORT.md"

    write_json(selector_path, packet)
    shortlisted_path.write_text(
        "".join(json.dumps(item, sort_keys=True) + "\n" for item in packet["review_items"]),
        encoding="utf-8",
    )
    report_path.write_text(manual_review_selector_to_markdown(packet), encoding="utf-8")
    return {
        "status": packet["status"],
        "packet": str(selector_path),
        "review_items": str(shortlisted_path),
        "report": str(report_path),
    }


def load_manual_review_selector(packet_path: str | Path) -> dict[str, Any]:
    payload = load_json(packet_path)
    if not isinstance(payload, dict):
        raise GuardrailError(f"Manual review selector packet must be a JSON object: {packet_path}")
    return payload

def classify_alias_review_item(item: Mapping[str, Any]) -> dict[str, Any]:
    """Classify a broad alias-review item using repo policy rules.

    This is intentionally conservative: it can promote obvious normalized-title
    candidates for later approval, but most policy-derived decisions are
    keep/manual-only with no live mutation authority.
    """

    target = _normalize_alias_text(item.get("target"))
    alias = _normalize_alias_text(item.get("alias"))
    rel_file = _normalize_alias_text(item.get("rel_file") or item.get("source") or item.get("file"))
    reason = _normalize_alias_text(item.get("reason"))
    bucket = _normalize_alias_text(item.get("bucket"))
    target_basename = _normalize_alias_text(item.get("target_basename") or Path(target).name)
    target_exists = bool(item.get("target_file_exists"))
    operator_decision = _normalize_alias_text(item.get("operator_decision"))
    user_required = item.get("user_required")

    policy_refs = [ALIAS_POLICY_REFS["selector_review_only"]]

    if _is_heading_anchor_target(target):
        return _alias_classification(
            decision="keep_alias_no_apply",
            policy_class="heading_anchor_alias_keep",
            reason="heading anchor / TOC style link; alias is intended display text",
            user_decision_required=False,
            policy_refs=[ALIAS_POLICY_REFS["generated_report_alias_keep"], *policy_refs],
        )

    if _is_protected_or_cross_vault_alias_path(target) or _is_protected_or_cross_vault_alias_path(rel_file):
        return _alias_classification(
            decision="manual_only_no_apply",
            policy_class="protected_or_cross_vault_manual",
            reason="protected/cross-vault/archive surface; keep out of automatic link cleanup",
            user_decision_required=False,
            policy_refs=[ALIAS_POLICY_REFS["protected_or_cross_vault_manual"], *policy_refs],
        )

    if _is_generated_report_alias_context(rel_file, target) or _is_generated_report_alias_context(
        _normalize_alias_text(item.get("context")),
        _normalize_alias_text(item.get("old") or item.get("candidate_rewrite_if_approved")),
    ):
        return _alias_classification(
            decision="keep_alias_no_apply",
            policy_class="generated_report_alias_keep",
            reason="generated/report navigation aliases are evidence display labels, not memory-note fixes",
            user_decision_required=False,
            policy_refs=[ALIAS_POLICY_REFS["generated_report_alias_keep"], *policy_refs],
        )

    if operator_decision == "keep_alias_no_apply" and user_required is False:
        return _alias_classification(
            decision="keep_alias_no_apply",
            policy_class="operator_review_keep_alias_no_apply",
            reason="operator reviewed alias and selected keep/no-apply; selector preserves the decision as evidence only",
            user_decision_required=False,
            policy_refs=[ALIAS_POLICY_REFS["operator_review_keep_alias_no_apply"], *policy_refs],
        )

    if reason == "normalized_title_match" and bucket == "safe_candidate_review_first" and target_exists:
        return _alias_classification(
            decision="safe_apply_candidate",
            policy_class="normalized_title_alias_removal_candidate",
            reason="alias is a normalized title variant of an existing target basename",
            user_decision_required=False,
            policy_refs=policy_refs,
        )

    if reason == "target_file_missing_or_unresolved":
        return _alias_classification(
            decision="keep_alias_no_apply",
            policy_class="unresolved_report_or_literal_alias_keep",
            reason="unresolved alias is not safe to retarget/create automatically",
            user_decision_required=False,
            policy_refs=policy_refs,
        )

    if _is_useful_semantic_alias(alias=alias, target_basename=target_basename, target=target):
        return _alias_classification(
            decision="keep_alias_no_apply",
            policy_class="semantic_short_alias_keep",
            reason="alias is a useful short/human display label for a longer canonical target",
            user_decision_required=False,
            policy_refs=policy_refs,
        )

    if reason == "alias_intent_differs_from_target_title":
        return _alias_classification(
            decision="manual_only_no_apply",
            policy_class="alias_intent_differs_manual_only",
            reason="alias meaning differs from target title; automatic removal would alter visible intent",
            user_decision_required=False,
            policy_refs=[ALIAS_POLICY_REFS["manual_review_only"], *policy_refs],
        )

    return _alias_classification(
        decision="needs_operator_review",
        policy_class="no_policy_match",
        reason="no conservative automatic policy matched",
        user_decision_required=True,
        policy_refs=policy_refs,
    )


def classify_alias_review_packet(packet: Mapping[str, Any]) -> dict[str, Any]:
    items = packet.get("items")
    if not isinstance(items, list):
        raise ValueError("alias review packet must contain an items list")

    classified: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    policy_counts: Counter[str] = Counter()
    user_required = 0
    for raw in items:
        if not isinstance(raw, Mapping):
            continue
        classification = classify_alias_review_item(raw)
        merged = dict(raw)
        merged["policy_classification"] = classification
        classified.append(merged)
        counts[str(classification["decision"])] += 1
        policy_counts[str(classification["policy_class"])] += 1
        if classification["user_decision_required"]:
            user_required += 1

    return {
        "schema": "obslayer.alias-policy-classification.v1",
        "mode": "repo-only/evidence-only",
        "source_schema": packet.get("schema"),
        "source_item_count": len(items),
        "classified_count": len(classified),
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "apply_authority": "none",
        "summary": {
            "decisions": dict(counts),
            "policy_classes": dict(policy_counts),
            "user_decision_required": user_required,
            "policy_refs": sorted({ref for item in classified for ref in item["policy_classification"]["policy_refs"]}),
        },
        "items": classified,
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }


def _alias_classification(
    *,
    decision: str,
    policy_class: str,
    reason: str,
    user_decision_required: bool,
    policy_refs: list[str],
) -> dict[str, Any]:
    risk = _alias_policy_risk(decision=decision, policy_class=policy_class)
    all_policy_refs = sorted({EXTERNAL_AUTOGRAPH_POLICY_REF, *policy_refs})
    return {
        "decision": decision,
        "policy_class": policy_class,
        "classification": policy_class,
        "risk": risk,
        "source_policy": _source_policy(f"alias-{policy_class}"),
        "reason": reason,
        "user_decision_required": user_decision_required,
        "live_apply_authorized": False,
        "apply_authority": "none",
        "policy_refs": all_policy_refs,
    }


def _alias_policy_risk(*, decision: str, policy_class: str) -> str:
    if decision == "safe_apply_candidate":
        return "low"
    if decision == "manual_only_no_apply" or "protected" in policy_class:
        return "high"
    if decision == "needs_operator_review":
        return "medium"
    return "low"


def _normalize_alias_text(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def _is_heading_anchor_target(target: str) -> bool:
    return target.startswith("#") or target.startswith("^") or "#" in target


def _is_generated_report_alias_context(rel_file: str, target: str) -> bool:
    rel_lower = rel_file.lower().replace("\\", "/")
    target_lower = target.lower().replace("\\", "/")
    return any(part in rel_lower or part in target_lower for part in GENERATED_REPORT_PATH_PARTS)


def _is_protected_or_cross_vault_alias_path(path: str) -> bool:
    lower = path.lower().replace("\\", "/")
    return any(part in lower for part in PROTECTED_LINK_PARTS) or lower.startswith("soul/")


def _is_useful_semantic_alias(*, alias: str, target_basename: str, target: str) -> bool:
    if not alias or not target_basename:
        return False
    normalized_basename = target_basename.removesuffix(".md").strip()
    basename_without_numeric_prefix = re.sub(r"^\d{2}[-_ ]+", "", normalized_basename).strip()
    if alias == basename_without_numeric_prefix and alias != normalized_basename:
        return True
    if DATE_TOKEN_RE.search(normalized_basename) and not DATE_TOKEN_RE.search(alias):
        return True
    alias_lower = alias.lower()
    basename_lower = normalized_basename.lower()
    if len(normalized_basename) - len(alias) >= 8 and alias_lower in basename_lower:
        return True
    if len(alias) - len(normalized_basename) >= 8 and basename_lower in alias_lower:
        return True
    target_lower = target.lower()
    if ("moc" in target_lower or "index" in target_lower) and len(alias) < len(normalized_basename):
        return True
    return False
