from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
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
    active_by_path: set[str] = set()
    title_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    shadows: list[dict[str, Any]] = []

    for note in notes:
        title_key = _title_key(note)
        if title_key:
            title_groups[title_key].append(note)

        if _shadow_kind(note):
            shadows.append(note)
            continue

        path = _path(note)
        if path:
            active_by_path.add(path)
        sha = _sha(note)
        if sha:
            active_by_sha[sha].append(path)
        if title_key:
            active_by_title[title_key].append(path)

    entries = [
        _entry_for_shadow(
            note=note,
            active_by_path=active_by_path,
            active_by_sha=active_by_sha,
            active_by_title=active_by_title,
            title_groups=title_groups,
        )
        for note in shadows
    ]
    entries.sort(
        key=lambda item: (
            SHADOW_KIND_ORDER.get(str(item["shadow_kind"]), 99),
            str(item["shadow_path"]),
        )
    )

    return {
        "version": "archive-shadow-index.v1",
        "mode": "repo-only/evidence-only",
        "behavior": "evidence-only",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "targets": [],
        "apply_authority": "none",
        "reason_codes": _ordered_reason_codes(entries),
        "entries": entries,
        "summary": _summary(entries),
    }


def write_archive_shadow_index(
    *,
    notes_index_jsonl: Path,
    out_dir: Path,
) -> dict[str, Any]:
    notes = read_notes_index_jsonl(notes_index_jsonl)
    index = build_archive_shadow_index(notes)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "archive-shadow-index.json"
    report_path = out_dir / "REPORT.md"
    json_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_report(index, source_path=notes_index_jsonl), encoding="utf-8")
    return {
        "archive_shadow_index": str(json_path),
        "report": str(report_path),
        "entries": len(index["entries"]),
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
    }


def read_notes_index_jsonl(path: Path) -> list[dict[str, Any]]:
    notes: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"Expected JSON object at {path}:{line_number}")
        notes.append(payload)
    return notes


def render_report(index: dict[str, Any], *, source_path: Path) -> str:
    summary = index["summary"]
    lines = [
        "# Archive Shadow Index v1",
        "",
        "Status: accepted evidence-only/proposal-only slice",
        f"Source: `{source_path}`",
        "",
        "Safety:",
        f"- `live_mutation_authorized`: `{str(index['live_mutation_authorized']).lower()}`",
        f"- `approval_manifest_created`: `{str(index['approval_manifest_created']).lower()}`",
        "- `targets`: `[]`",
        "- `apply_authority`: `none`",
        "",
        "Summary:",
        f"- entries: {summary['entries']}",
        f"- archive: {summary['by_kind'].get('archive', 0)}",
        f"- backup: {summary['by_kind'].get('backup', 0)}",
        f"- duplicate: {summary['by_kind'].get('duplicate', 0)}",
        f"- redirect: {summary['by_kind'].get('redirect', 0)}",
        f"- with active path: {summary['with_active_path']}",
        f"- shadow only: {summary['shadow_only']}",
        "",
        "Reason codes:",
    ]
    lines.extend(f"- `{code}`" for code in index["reason_codes"])
    lines.extend(
        [
            "",
            "Boundary:",
            "Archive, backup, duplicate, and redirect entries are evidence-only shadows.",
            "A `shadow_path` is never emitted as an active target.",
            "",
        ]
    )
    return "\n".join(lines)


def _entry_for_shadow(
    *,
    note: dict[str, Any],
    active_by_path: set[str],
    active_by_sha: dict[str, list[str]],
    active_by_title: dict[str, list[str]],
    title_groups: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    shadow_kind = _shadow_kind(note) or "archive"
    active_path = _active_path(note, active_by_path, active_by_sha, active_by_title)
    reason_codes = _entry_reason_codes(
        shadow_kind=shadow_kind,
        active_path=active_path,
        duplicate_title=_has_duplicate_title(note, title_groups),
    )
    return {
        "active_path": active_path,
        "shadow_path": _path(note),
        "shadow_kind": shadow_kind,
        "sha256": _sha(note) or None,
        "title": str(note.get("title") or ""),
        "reason_codes": reason_codes,
        "behavior": "evidence-only",
        "target_authority": "none",
    }


def _active_path(
    note: dict[str, Any],
    active_by_path: set[str],
    active_by_sha: dict[str, list[str]],
    active_by_title: dict[str, list[str]],
) -> str | None:
    hinted_path = str(note.get("canonical_path") or note.get("duplicate_of") or "")
    if hinted_path in active_by_path:
        return hinted_path

    sha = _sha(note)
    if sha:
        active_paths = [path for path in active_by_sha.get(sha, []) if path != _path(note)]
        if active_paths:
            return active_paths[0]

    title_key = _title_key(note)
    if title_key:
        active_paths = [path for path in active_by_title.get(title_key, []) if path != _path(note)]
        if active_paths:
            return active_paths[0]

    return None


def _entry_reason_codes(
    *,
    shadow_kind: str,
    active_path: str | None,
    duplicate_title: bool,
) -> list[str]:
    reason_codes: set[str] = set()
    if active_path:
        reason_codes.add("active_target_available")
    else:
        reason_codes.add("archive_shadow_only")
    if shadow_kind in {"archive", "backup"} and active_path:
        reason_codes.add("memory_plus_archive_collision")
    if shadow_kind == "redirect":
        reason_codes.add("redirect_collision")
    if duplicate_title or shadow_kind == "duplicate":
        reason_codes.add("duplicate_title_group")
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


def _summary(entries: list[dict[str, Any]]) -> dict[str, Any]:
    by_kind: dict[str, int] = {kind: 0 for kind in SHADOW_KIND_ORDER}
    with_active_path = 0
    for entry in entries:
        by_kind[str(entry["shadow_kind"])] = by_kind.get(str(entry["shadow_kind"]), 0) + 1
        if entry["active_path"]:
            with_active_path += 1
    return {
        "entries": len(entries),
        "by_kind": by_kind,
        "with_active_path": with_active_path,
        "shadow_only": len(entries) - with_active_path,
    }


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
