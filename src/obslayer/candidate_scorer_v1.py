from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

MODE = "candidate-scorer-v1"
DEFAULT_LANE = "active_memory_ambiguous_memory_plus_archive"

REASON_CODE_ORDER = [
    "candidate_scorer_evidence_only",
    "active_target_available",
    "exact_path_match",
    "exact_title_match",
    "alias_match",
    "same_top_level",
    "folder_locality_match",
    "backlink_support",
    "outlink_support",
    "tag_compatibility",
    "frontmatter_compatibility",
    "previous_operator_accept_prior",
    "previous_operator_reject_prior",
    "previous_operator_held_prior",
    "ambiguous_candidates",
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
]

SHADOW_KIND_ORDER = {
    "archive": 0,
    "backup": 1,
    "trash": 2,
    "duplicate": 3,
    "redirect": 4,
}


def score_candidate(
    *,
    link: dict[str, Any],
    notes_by_path: dict[str, dict[str, Any]],
    graph_support_by_path: Mapping[str, Mapping[str, Any]] | None = None,
    operator_decision_priors: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source = str(link.get("source", ""))
    status = link.get("status")
    source_note = notes_by_path.get(source)
    source_archive = _is_archive_surface(source_note, source)
    source_soul = _is_soul_surface(source_note, source)
    source_sensitive = source_archive or source_soul or _is_canonical_surface(source_note, source)
    candidates = [str(candidate_path) for candidate_path in link.get("candidates") or []]
    link_requires_review = status in {"ambiguous", "broken"} or len(candidates) != 1 or source_sensitive
    scored: list[dict[str, Any]] = []
    graph_support = graph_support_by_path or {}
    priors = operator_decision_priors or _operator_decision_priors_from_link(link)

    for candidate_path in candidates:
        path = str(candidate_path)
        note = notes_by_path.get(path)
        scored.append(
            _score_one(
                path=path,
                note=note,
                source=source,
                source_note=source_note,
                status=status,
                target_hint=str(link.get("target") or link.get("raw") or link.get("old_link") or link.get("old_text") or ""),
                source_archive=source_archive,
                source_soul=source_soul,
                link_requires_review=link_requires_review,
                graph_features=dict(graph_support.get(path) or {}),
                operator_decision_prior=priors.get(path),
            )
        )

    scored.sort(key=lambda item: (-int(item["score"]), item["path"]))
    top_two_gap = 0
    if len(scored) >= 2:
        top_two_gap = int(scored[0]["score"]) - int(scored[1]["score"])

    hard_stop = any(bool(item["hard_stop"]) for item in scored)
    review_required = link_requires_review or hard_stop
    reason_codes = {"candidate_scorer_evidence_only"}
    safety_flags: set[str] = {"evidence_only", "no_live_apply"}
    if source_archive:
        reason_codes.add("source_archive_surface")
        safety_flags.add("source_archive_surface")
    if source_soul:
        reason_codes.add("source_soul_surface")
        safety_flags.add("soul_policy_sensitive")
    for item in scored:
        reason_codes.update(str(code) for code in item["reason_codes"])
        safety_flags.update(str(flag) for flag in item["safety_flags"])
    if link_requires_review:
        reason_codes.add("ambiguous_candidates")
    if review_required:
        reason_codes.add("operator_review_required")
        safety_flags.add("operator_review_required")
    if hard_stop:
        reason_codes.add("unsafe_candidate_hard_stop")
        safety_flags.add("hard_stop_candidate_present")

    return {
        "mode": MODE,
        "behavior": "evidence-only",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "targets": [],
        "apply_authority": "none",
        "source": source,
        "status": status,
        "old_link": link.get("raw", link.get("old_link")),
        "target_hint": link.get("target"),
        "top_two_gap": top_two_gap,
        "review_required": review_required,
        "hard_stop": hard_stop,
        "route_hint": _route_hint(scored, review_required=review_required, hard_stop=hard_stop, top_two_gap=top_two_gap),
        "reason_codes": _ordered_reason_codes(reason_codes),
        "safety_flags": sorted(safety_flags),
        "candidates": scored,
    }


def build_candidate_scorer_packet(
    *,
    actionable_lanes_json: str | Path | None = None,
    notes_index_jsonl: str | Path,
    wikilinks_jsonl: str | Path,
    lane: str = DEFAULT_LANE,
    packet_id: str | None = None,
    created_at: str | None = None,
    limit: int | None = None,
    operator_decision_records: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    lanes = _read_json(actionable_lanes_json) if actionable_lanes_json is not None else {}
    notes = read_jsonl(notes_index_jsonl)
    wikilinks = read_jsonl(wikilinks_jsonl)
    notes_by_path = {str(note.get("path", "")): note for note in notes}
    inbound_mentions = _candidate_inbound_mentions(wikilinks)
    priors = _operator_decision_priors(operator_decision_records or [])
    effective_lane = lane if actionable_lanes_json is not None else "all"
    selected_links = [
        link
        for link in wikilinks
        if (link.get("candidates") or []) and _link_matches_lane(link, notes_by_path=notes_by_path, lane=effective_lane)
    ]
    selected_links.sort(key=lambda item: (str(item.get("source") or ""), str(item.get("raw") or item.get("target") or "")))
    if limit is not None:
        selected_links = selected_links[:limit]

    scored_links = [
        score_candidate(
            link=link,
            notes_by_path=notes_by_path,
            graph_support_by_path=_graph_support_for_link(link, notes_by_path=notes_by_path, inbound_mentions=inbound_mentions),
            operator_decision_priors=priors,
        )
        for link in selected_links
    ]
    reason_codes = {"candidate_scorer_evidence_only"}
    safety_flags = {"evidence_only", "no_live_apply", "approval_manifest_creation_forbidden"}
    for scored in scored_links:
        reason_codes.update(str(code) for code in scored.get("reason_codes", []))
        safety_flags.update(str(flag) for flag in scored.get("safety_flags", []))

    return {
        "schema": MODE,
        "mode": "repo-only/evidence-only",
        "status": "ok",
        "packet_id": packet_id or f"candidate-scorer-v1-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}",
        "created_at": created_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_actionable_lanes": str(Path(actionable_lanes_json)) if actionable_lanes_json is not None else None,
        "source_notes_index": str(Path(notes_index_jsonl)),
        "source_wikilinks": str(Path(wikilinks_jsonl)),
        "lane": effective_lane,
        "source_lane_count": _source_lane_count(lanes, lane),
        "behavior": "evidence-only",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "targets": [],
        "apply_authority": "none",
        "reason_codes": _ordered_reason_codes(reason_codes),
        "safety_flags": sorted(safety_flags),
        "summary": _packet_summary(scored_links),
        "candidate_packets": scored_links,
        "scored_links": scored_links,
    }


def write_candidate_scorer_packet(
    *,
    actionable_lanes_json: str | Path | None = None,
    notes_index_jsonl: str | Path,
    wikilinks_jsonl: str | Path,
    out_dir: str | Path,
    lane: str = DEFAULT_LANE,
    packet_id: str | None = None,
    limit: int | None = None,
    operator_decision_records: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    packet = build_candidate_scorer_packet(
        actionable_lanes_json=actionable_lanes_json,
        notes_index_jsonl=notes_index_jsonl,
        wikilinks_jsonl=wikilinks_jsonl,
        lane=lane,
        packet_id=packet_id,
        limit=limit,
        operator_decision_records=operator_decision_records,
    )
    packet_dir = Path(out_dir)
    packet_dir.mkdir(parents=True, exist_ok=True)
    packet_path = packet_dir / "candidate-scorer-v1.json"
    jsonl_path = packet_dir / "candidates.jsonl"
    report_path = packet_dir / "REPORT.md"
    packet_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    jsonl_path.write_text(
        "".join(json.dumps(item, sort_keys=True) + "\n" for item in packet["scored_links"]),
        encoding="utf-8",
    )
    report_path.write_text(candidate_scorer_packet_to_markdown(packet), encoding="utf-8")
    return {
        "status": "ok",
        "candidate_scorer": str(packet_path),
        "report": str(report_path),
    }


def candidate_scorer_packet_to_markdown(packet: Mapping[str, Any]) -> str:
    summary = packet["summary"]
    lines = [
        "# Candidate scorer v1",
        "",
        "Status: evidence-only/proposal-only scorer packet",
        f"Packet id: `{packet['packet_id']}`",
        f"Created at: `{packet['created_at']}`",
        f"Lane: `{packet['lane']}`",
        "",
        "## Safety",
        "",
        f"- live_mutation_authorized: `{str(packet['live_mutation_authorized']).lower()}`",
        f"- approval_manifest_created: `{str(packet['approval_manifest_created']).lower()}`",
        f"- approval_manifest_authority: `{str(packet['approval_manifest_authority']).lower()}`",
        "- targets: `[]`",
        "- apply_authority: `none`",
        "",
        "## Summary",
        "",
        f"- source_lane_count: `{packet['source_lane_count']}`",
        f"- candidate_packets: `{summary['candidate_packets']}`",
        f"- scored_links: `{summary['scored_links']}`",
        f"- candidate_count: `{summary['candidate_count']}`",
        f"- review_required_links: `{summary['review_required_links']}`",
        f"- hard_stop_packets: `{summary['hard_stop_packets']}`",
        f"- hard_stop_links: `{summary['hard_stop_links']}`",
        f"- max_top_two_gap: `{summary['max_top_two_gap']}`",
        "",
        "## Route hints",
        "",
    ]
    lines.extend(f"- `{route}`: `{count}`" for route, count in summary["route_hints"].items())
    lines.extend(["", "## Reason codes", ""])
    lines.extend(f"- `{code}`" for code in packet["reason_codes"])
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This packet ranks link-fix candidates from generated index evidence only.",
            "It grants no apply authority, does not mutate a live vault, create approval manifests, or emit live apply targets.",
            "Soul, archive, backup, duplicate, redirect, canonical, missing, and ambiguous surfaces remain human-gated.",
            "",
        ]
    )
    return "\n".join(lines)


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    path = Path(path)
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"Expected JSON object at {path}:{line_number}")
        records.append(payload)
    return records


def _score_one(
    *,
    path: str,
    note: dict[str, Any] | None,
    source: str,
    source_note: dict[str, Any] | None,
    status: Any,
    target_hint: str,
    source_archive: bool,
    source_soul: bool,
    link_requires_review: bool,
    graph_features: dict[str, Any],
    operator_decision_prior: Any,
) -> dict[str, Any]:
    score = 74
    source_archive_penalty = -25 if source_archive else 0
    candidate_archive_penalty = 0
    feature_points: dict[str, int] = {}
    reason_codes: set[str] = set()
    safety_flags: set[str] = set()
    hard_stop = False

    if source_archive:
        reason_codes.add("source_archive_surface")
        safety_flags.add("source_archive_surface")
    if source_soul:
        reason_codes.add("source_soul_surface")
        safety_flags.add("soul_policy_sensitive")

    if link_requires_review:
        safety_flags.add("ambiguous_link_requires_review")

    if note is None:
        candidate_archive_penalty -= 80
        hard_stop = True
        reason_codes.add("candidate_missing_from_index")
        safety_flags.add("candidate_missing_requires_review")
    else:
        shadow_kind = _shadow_kind(note, path)
        target_soul = _is_soul_surface(note, path)
        canonical = _is_canonical_surface(note, path)
        if shadow_kind is None and not target_soul and not canonical:
            reason_codes.add("active_target_available")
        if shadow_kind is not None:
            hard_stop = True
            safety_flags.add("archive_or_shadow_target_hard_stop")
            candidate_archive_penalty += _shadow_penalty(shadow_kind)
            reason_codes.update(_shadow_reason_codes(shadow_kind, note))
        if target_soul:
            hard_stop = True
            reason_codes.add("target_soul_surface")
            reason_codes.add("soul_or_protected_surface")
            safety_flags.add("soul_policy_sensitive")
            safety_flags.add("soul_or_protected_surface_hard_stop")
        if canonical:
            hard_stop = True
            reason_codes.add("canonical_or_global_surface")
            safety_flags.add("canonical_or_global_requires_review")

        feature_points.update(_feature_points(path=path, note=note, source=source, source_note=source_note, target_hint=target_hint))
        feature_points.update(_graph_feature_points(note=note, graph_features=graph_features))
        prior_points, prior_code = _operator_prior_points(operator_decision_prior)
        if prior_code:
            reason_codes.add(prior_code)
            feature_points["operator_decision_prior"] = prior_points
        reason_codes.update(_feature_reason_codes(feature_points))

    score += source_archive_penalty + candidate_archive_penalty + sum(feature_points.values())
    review_required = link_requires_review or hard_stop
    if review_required:
        reason_codes.add("operator_review_required")

    return {
        "path": path,
        "score": score,
        "confidence": _confidence(score),
        "review_required": review_required,
        "hard_stop": hard_stop,
        "reason_codes": _ordered_reason_codes(reason_codes),
        "safety_flags": sorted(safety_flags),
        "feature_breakdown": {
            "status": status,
            "source": source,
            "source_archive_penalty": source_archive_penalty,
            "candidate_archive_penalty": candidate_archive_penalty,
            "candidate_shadow_kind": _shadow_kind(note, path) if note is not None else "missing",
            **feature_points,
            "graph_features": graph_features,
        },
    }


def _read_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _feature_points(
    *,
    path: str,
    note: dict[str, Any],
    source: str,
    source_note: dict[str, Any] | None,
    target_hint: str,
) -> dict[str, int]:
    points: dict[str, int] = {}
    normalized_target = _normalize_target(target_hint)
    path_key = _strip_md(path).lower()
    title_key = _title(note, path).lower()
    if normalized_target and normalized_target in {path_key, path.lower()}:
        points["exact_path_match"] = 20
    if normalized_target and normalized_target.split("/")[-1] == title_key:
        points["exact_title_match"] = 18
    if normalized_target and normalized_target in {_normalize_text(alias) for alias in _aliases(note)}:
        points["alias_match"] = 18
    if source_note and str(source_note.get("top") or source.split("/", 1)[0]) == str(note.get("top") or path.split("/", 1)[0]):
        points["same_top_level"] = 8
    if _folder(path) and _folder(path) == _folder(source):
        points["folder_locality_match"] = 6
    source_tags = _string_set(source_note.get("tags") if source_note else [])
    target_tags = _string_set(note.get("tags") or [])
    tag_overlap = source_tags & target_tags
    if tag_overlap:
        points["tag_compatibility"] = min(6, len(tag_overlap) * 3)
    source_frontmatter = _string_set(source_note.get("frontmatter_keys") if source_note else [])
    target_frontmatter = _string_set(note.get("frontmatter_keys") or [])
    frontmatter_overlap = source_frontmatter & target_frontmatter
    if frontmatter_overlap:
        points["frontmatter_compatibility"] = min(4, len(frontmatter_overlap) * 2)
    return points


def _graph_feature_points(*, note: dict[str, Any], graph_features: dict[str, Any]) -> dict[str, int]:
    points: dict[str, int] = {}
    inbound = int(graph_features.get("candidate_inbound_mentions") or note.get("backlink_count") or note.get("inbound_link_count") or 0)
    outlinks = int(graph_features.get("candidate_outlinks") or note.get("wikilink_count") or 0)
    if inbound > 0:
        points["backlink_support"] = min(10, inbound)
    if outlinks > 0:
        points["outlink_support"] = min(5, max(1, outlinks // 10))
    return points


def _feature_reason_codes(feature_points: Mapping[str, int]) -> set[str]:
    return {code for code in feature_points if code in REASON_CODE_ORDER and feature_points[code] != 0}


def _shadow_reason_codes(shadow_kind: str, note: dict[str, Any]) -> set[str]:
    reason_codes: set[str] = set()
    if shadow_kind in {"archive", "backup", "trash"}:
        reason_codes.add("protected_or_archive_target")
    if shadow_kind == "archive":
        reason_codes.add("archive_shadow_target")
    elif shadow_kind == "backup":
        reason_codes.add("backup_shadow_target")
    elif shadow_kind == "trash":
        reason_codes.add("trash_shadow_target")
    elif shadow_kind == "duplicate":
        reason_codes.add("duplicate_shadow_target")
    elif shadow_kind == "redirect":
        reason_codes.add("redirect_shadow_target")
    if note.get("canonical_path"):
        reason_codes.add("canonical_shadow_target")
    return reason_codes


def _shadow_penalty(shadow_kind: str) -> int:
    return {
        "archive": -100,
        "backup": -100,
        "trash": -100,
        "duplicate": -90,
        "redirect": -90,
    }.get(shadow_kind, -75)


def _shadow_kind(note: dict[str, Any], path: str) -> str | None:
    top = str(note.get("top") or path.split("/", 1)[0])
    if top == "Redirects" or path.startswith("Redirects/") or note.get("canonical_path"):
        return "redirect"
    if top == "Duplicates" or path.startswith("Duplicates/") or note.get("duplicate_of"):
        return "duplicate"
    if top == "_Backups" or path.startswith("_Backups/"):
        return "backup"
    if top == ".trash" or path.startswith(".trash/"):
        return "trash"
    if top == "_Archive" or path.startswith("_Archive/") or note.get("protected_or_archive_surface"):
        return "archive"
    return None


def _is_archive_surface(note: dict[str, Any] | None, path: str) -> bool:
    if note is None:
        return path.startswith(("_Archive/", "_Backups/", ".trash/"))
    return _shadow_kind(note, path) in {"archive", "backup", "trash"}


def _is_soul_surface(note: dict[str, Any] | None, path: str) -> bool:
    top = str((note or {}).get("top") or path.split("/", 1)[0])
    return top.startswith("Soul") or path.startswith(("Soul/", "Soul-Vault/", "Soul-Organism-Graphify-Vault/"))


def _is_canonical_surface(note: dict[str, Any] | None, path: str) -> bool:
    top = str((note or {}).get("top") or path.split("/", 1)[0])
    lowered = path.lower()
    return bool(top == "Canonical" or lowered.startswith("canonical/") or (note or {}).get("canonical_path"))


def _ordered_reason_codes(reason_codes: set[str]) -> list[str]:
    order = {reason_code: index for index, reason_code in enumerate(REASON_CODE_ORDER)}
    return sorted(reason_codes, key=lambda code: (order.get(code, len(order)), code))


def _confidence(score: int) -> float:
    return round(max(0.0, min(1.0, score / 100)), 3)


def _normalize_target(value: str) -> str:
    target = value.split("|", 1)[0].strip("[] ")
    return _strip_md(target).lower()


def _normalize_text(value: Any) -> str:
    return _strip_md(str(value)).lower()


def _strip_md(path: str) -> str:
    return path[:-3] if path.endswith(".md") else path


def _title(note: Mapping[str, Any], path: str) -> str:
    return str(note.get("title") or note.get("stem") or Path(path).stem)


def _aliases(note: Mapping[str, Any]) -> list[str]:
    aliases = note.get("aliases", note.get("alias", []))
    if isinstance(aliases, str):
        return [aliases]
    if isinstance(aliases, Iterable):
        return [str(alias) for alias in aliases]
    return []


def _folder(path: str) -> str:
    return str(Path(path).parent) if "/" in path else ""


def _string_set(value: Any) -> set[str]:
    if not value:
        return set()
    if isinstance(value, str):
        return {value}
    if isinstance(value, Iterable):
        return {str(item) for item in value if str(item)}
    return set()


def _operator_decision_priors(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    priors: dict[str, Any] = {}
    for record in records:
        target = str(record.get("target") or record.get("proposed_target") or record.get("candidate_path") or "")
        decision = record.get("decision", record.get("decision_type"))
        if target and decision:
            priors[target] = decision
    return priors


def _operator_decision_priors_from_link(link: Mapping[str, Any]) -> dict[str, Any]:
    raw = link.get("operator_decision_prior") or link.get("operator_decision_priors") or {}
    if isinstance(raw, Mapping):
        return {str(key): value for key, value in raw.items()}
    if isinstance(raw, Iterable) and not isinstance(raw, str):
        return _operator_decision_priors(item for item in raw if isinstance(item, Mapping))
    return {}


def _operator_prior_points(prior: Any) -> tuple[int, str | None]:
    value = str(prior or "").lower()
    if "accept" in value or value == "approved":
        return 10, "previous_operator_accept_prior"
    if "reject" in value or "deny" in value:
        return -40, "previous_operator_reject_prior"
    if "hold" in value or "held" in value or "defer" in value:
        return -15, "previous_operator_held_prior"
    return 0, None


def _candidate_inbound_mentions(wikilinks: Iterable[Mapping[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for link in wikilinks:
        for candidate in link.get("candidates") or []:
            counts[str(candidate)] += 1
    return counts


def _graph_support_for_link(
    link: Mapping[str, Any],
    *,
    notes_by_path: Mapping[str, Mapping[str, Any]],
    inbound_mentions: Counter[str],
) -> dict[str, dict[str, Any]]:
    support: dict[str, dict[str, Any]] = {}
    for candidate in link.get("candidates") or []:
        path = str(candidate)
        note = notes_by_path.get(path) or {}
        support[path] = {
            "candidate_inbound_mentions": inbound_mentions[path],
            "candidate_outlinks": note.get("wikilink_count", 0),
        }
    return support


def _link_matches_lane(link: Mapping[str, Any], *, notes_by_path: Mapping[str, dict[str, Any]], lane: str) -> bool:
    if lane in {"all", "*"}:
        return True
    source = str(link.get("source") or "")
    source_note = notes_by_path.get(source)
    source_class = _source_class(source_note, source)
    status = str(link.get("status") or "")
    candidate_classes = {_candidate_class(notes_by_path.get(str(candidate)), str(candidate)) for candidate in link.get("candidates") or []}
    if lane == "active_memory_ambiguous_memory_plus_archive":
        return (
            source_class == "active_memory_source"
            and status == "ambiguous"
            and "memory" in candidate_classes
            and "archive" in candidate_classes
        )
    if lane in {"active_memory_broken", "active_memory_broken_links"}:
        return source_class == "active_memory_source" and status == "broken"
    if lane == "archive_or_backup_noise":
        return source_class == "archive_or_backup_source"
    if lane == "active_soul_source":
        return source_class == "active_soul_source"
    return False


def _source_class(note: Mapping[str, Any] | None, path: str) -> str:
    top = str((note or {}).get("top") or path.split("/", 1)[0])
    if _is_archive_surface(dict(note or {}), path):
        return "archive_or_backup_source"
    if top.startswith("Soul"):
        return "active_soul_source"
    if top.startswith("Memory"):
        return "active_memory_source"
    if "Graphify" in top or path.startswith("Soul-Organism-Graphify-Vault/"):
        return "graphify_vault_source"
    return "unknown_source"


def _candidate_class(note: Mapping[str, Any] | None, path: str) -> str:
    if _is_archive_surface(dict(note or {}), path) or _shadow_kind(dict(note or {}), path):
        return "archive"
    if _is_soul_surface(dict(note or {}), path):
        return "active_soul"
    if path.startswith("Memory-Vault/"):
        return "memory"
    if "Graphify" in path:
        return "graphify"
    return "other"


def _source_lane_count(lanes: Mapping[str, Any], lane: str) -> int:
    for item in lanes.get("next_lanes") or []:
        if isinstance(item, Mapping) and item.get("lane") == lane:
            return int(item.get("count") or 0)
    return 0


def _packet_summary(scored_links: list[dict[str, Any]]) -> dict[str, Any]:
    route_counts: Counter[str] = Counter(str(link.get("route_hint") or "unknown") for link in scored_links)
    return {
        "candidate_packets": len(scored_links),
        "scored_links": len(scored_links),
        "candidate_count": sum(len(link.get("candidates", [])) for link in scored_links),
        "review_required_packets": sum(1 for link in scored_links if link.get("review_required")),
        "review_required_links": sum(1 for link in scored_links if link.get("review_required")),
        "hard_stop_packets": sum(1 for link in scored_links if link.get("hard_stop")),
        "hard_stop_links": sum(1 for link in scored_links if link.get("hard_stop")),
        "max_top_two_gap": max((int(link.get("top_two_gap") or 0) for link in scored_links), default=0),
        "route_hints": dict(sorted(route_counts.items())),
    }


def _route_hint(scored: list[dict[str, Any]], *, review_required: bool, hard_stop: bool, top_two_gap: int) -> str:
    if hard_stop:
        return "blocked/refuse"
    top_confidence = float(scored[0]["confidence"]) if scored else 0.0
    if review_required:
        return "needs-human-review"
    if top_confidence >= 0.95 and top_two_gap >= 20:
        return "auto-propose"
    return "suggest"
