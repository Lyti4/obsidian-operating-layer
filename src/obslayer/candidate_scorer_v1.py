from __future__ import annotations

from typing import Any

REASON_CODE_ORDER = [
    "candidate_scorer_evidence_only",
    "active_target_available",
    "ambiguous_candidates",
    "source_archive_surface",
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
) -> dict[str, Any]:
    source = str(link.get("source", ""))
    status = link.get("status")
    source_note = notes_by_path.get(source)
    source_archive = _is_archive_surface(source_note, source)
    link_requires_review = status in {"ambiguous", "broken"} or len(link.get("candidates") or []) != 1
    scored: list[dict[str, Any]] = []

    for candidate_path in link.get("candidates") or []:
        path = str(candidate_path)
        note = notes_by_path.get(path)
        scored.append(
            _score_one(
                path=path,
                note=note,
                source=source,
                status=status,
                source_archive=source_archive,
                link_requires_review=link_requires_review,
            )
        )

    scored.sort(key=lambda item: (-int(item["score"]), item["path"]))
    top_two_gap = 0
    if len(scored) >= 2:
        top_two_gap = int(scored[0]["score"]) - int(scored[1]["score"])

    hard_stop = any(bool(item["hard_stop"]) for item in scored)
    review_required = link_requires_review or hard_stop
    reason_codes = {"candidate_scorer_evidence_only"}
    for item in scored:
        reason_codes.update(str(code) for code in item["reason_codes"])
    if link_requires_review:
        reason_codes.add("ambiguous_candidates")
    if review_required:
        reason_codes.add("operator_review_required")
    if hard_stop:
        reason_codes.add("unsafe_candidate_hard_stop")

    return {
        "behavior": "evidence-only",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "source": source,
        "status": status,
        "top_two_gap": top_two_gap,
        "review_required": review_required,
        "hard_stop": hard_stop,
        "reason_codes": _ordered_reason_codes(reason_codes),
        "candidates": scored,
    }


def _score_one(
    *,
    path: str,
    note: dict[str, Any] | None,
    source: str,
    status: Any,
    source_archive: bool,
    link_requires_review: bool,
) -> dict[str, Any]:
    score = 100
    source_archive_penalty = -25 if source_archive else 0
    candidate_archive_penalty = 0
    reason_codes: set[str] = set()
    safety_flags: set[str] = set()
    hard_stop = False

    if source_archive:
        reason_codes.add("source_archive_surface")
        safety_flags.add("source_archive_surface")

    if link_requires_review:
        safety_flags.add("ambiguous_link_requires_review")

    if note is None:
        candidate_archive_penalty -= 80
        hard_stop = True
        reason_codes.add("candidate_missing_from_index")
        safety_flags.add("candidate_missing_requires_review")
    else:
        shadow_kind = _shadow_kind(note, path)
        if shadow_kind is None:
            reason_codes.add("active_target_available")
        else:
            hard_stop = True
            safety_flags.add("archive_or_shadow_target_hard_stop")
            candidate_archive_penalty += _shadow_penalty(shadow_kind)
            reason_codes.update(_shadow_reason_codes(shadow_kind, note))

    score += source_archive_penalty + candidate_archive_penalty
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
        },
    }


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
        return False
    return _shadow_kind(note, path) in {"archive", "backup", "trash"}


def _ordered_reason_codes(reason_codes: set[str]) -> list[str]:
    order = {reason_code: index for index, reason_code in enumerate(REASON_CODE_ORDER)}
    return sorted(reason_codes, key=lambda code: (order.get(code, len(order)), code))


def _confidence(score: int) -> float:
    return round(max(0.0, min(1.0, score / 100)), 3)
