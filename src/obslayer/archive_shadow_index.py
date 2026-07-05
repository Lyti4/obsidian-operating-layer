from __future__ import annotations

from collections import defaultdict
from typing import Any

REASON_CODE_ORDER = [
    "active_target_available",
    "archive_shadow_only",
    "memory_plus_archive_collision",
    "redirect_collision",
    "duplicate_title_group",
]

SHADOW_KIND_ORDER = {
    "archive": 0,
    "backup": 1,
    "duplicate": 2,
    "redirect": 3,
}


def build_archive_shadow_index(notes: list[dict[str, Any]]) -> dict[str, Any]:
    active_by_sha: dict[str, list[str]] = defaultdict(list)
    active_by_title: dict[str, list[str]] = defaultdict(list)
    title_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    shadows: list[dict[str, Any]] = []

    for note in notes:
        path = _path(note)
        title_key = _title_key(note)
        if title_key:
            title_groups[title_key].append(note)
        if _shadow_kind(note):
            shadows.append(note)
            continue
        sha = _sha(note)
        if sha:
            active_by_sha[sha].append(path)
        if title_key:
            active_by_title[title_key].append(path)

    entries = []
    for note in shadows:
        shadow_kind = _shadow_kind(note) or "archive"
        active_path = _active_path(note, active_by_sha, active_by_title)
        reason_codes = _entry_reason_codes(
            note=note,
            shadow_kind=shadow_kind,
            active_path=active_path,
            duplicate_title=_has_duplicate_title(note, title_groups),
        )
        entries.append(
            {
                "active_path": active_path,
                "shadow_path": _path(note),
                "shadow_kind": shadow_kind,
                "sha256": _sha(note),
                "reason_codes": reason_codes,
                "behavior": "evidence-only",
            }
        )

    entries.sort(
        key=lambda item: (
            SHADOW_KIND_ORDER.get(str(item["shadow_kind"]), 99),
            str(item["shadow_path"]),
            str(item["active_path"] or ""),
        )
    )
    return {
        "behavior": "evidence-only",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "reason_codes": _ordered_reason_codes(entries),
        "entries": entries,
    }


def _active_path(
    note: dict[str, Any],
    active_by_sha: dict[str, list[str]],
    active_by_title: dict[str, list[str]],
) -> str | None:
    explicit_path = str(note.get("canonical_path") or note.get("duplicate_of") or "")
    if explicit_path:
        return explicit_path
    sha = _sha(note)
    if sha and active_by_sha.get(sha):
        return active_by_sha[sha][0]
    title_key = _title_key(note)
    if title_key and active_by_title.get(title_key):
        return active_by_title[title_key][0]
    return None


def _entry_reason_codes(
    *,
    note: dict[str, Any],
    shadow_kind: str,
    active_path: str | None,
    duplicate_title: bool,
) -> list[str]:
    reason_codes = []
    if active_path:
        reason_codes.append("active_target_available")
    else:
        reason_codes.append("archive_shadow_only")
    if shadow_kind in {"archive", "backup"} and active_path:
        reason_codes.append("memory_plus_archive_collision")
    if shadow_kind == "redirect":
        reason_codes.append("redirect_collision")
    if duplicate_title:
        reason_codes.append("duplicate_title_group")
    return _sort_reason_codes(reason_codes)


def _has_duplicate_title(
    note: dict[str, Any],
    title_groups: dict[str, list[dict[str, Any]]],
) -> bool:
    title_key = _title_key(note)
    return bool(title_key and len(title_groups[title_key]) > 1)


def _ordered_reason_codes(entries: list[dict[str, Any]]) -> list[str]:
    found = {
        code
        for entry in entries
        for code in entry.get("reason_codes", [])
        if isinstance(code, str)
    }
    return _sort_reason_codes(found)


def _sort_reason_codes(reason_codes: set[str] | list[str]) -> list[str]:
    return [code for code in REASON_CODE_ORDER if code in reason_codes]


def _shadow_kind(note: dict[str, Any]) -> str | None:
    path = _path(note)
    top = str(note.get("top") or path.split("/", 1)[0])
    if top == "Redirects" or path.startswith("Redirects/") or note.get("canonical_path"):
        return "redirect"
    if top == "Duplicates" or path.startswith("Duplicates/") or note.get("duplicate_of"):
        return "duplicate"
    if top == "_Backups" or path.startswith("_Backups/"):
        return "backup"
    if (
        top in {"_Archive", ".trash"}
        or path.startswith(("_Archive/", ".trash/"))
        or note.get("protected_or_archive_surface")
    ):
        return "archive"
    return None


def _path(note: dict[str, Any]) -> str:
    return str(note.get("path") or "")


def _sha(note: dict[str, Any]) -> str:
    return str(note.get("sha256") or "")


def _title_key(note: dict[str, Any]) -> str:
    title = str(note.get("title") or "")
    if not title:
        title = _path(note).rsplit("/", 1)[-1].removesuffix(".md")
    return title.casefold()
