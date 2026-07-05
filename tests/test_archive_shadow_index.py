from __future__ import annotations

import json

from obslayer.archive_shadow_index import build_archive_shadow_index, write_archive_shadow_index


def _notes() -> list[dict[str, object]]:
    return [
        {
            "path": "Memory-Vault/A.md",
            "top": "Memory-Vault",
            "sha256": "same",
            "title": "A",
        },
        {
            "path": "Memory-Vault/Backup Match.md",
            "top": "Memory-Vault",
            "sha256": "backup-same",
            "title": "Backup Match",
        },
        {
            "path": "Memory-Vault/Canonical.md",
            "top": "Memory-Vault",
            "sha256": "canonical",
            "title": "Canonical",
        },
        {
            "path": "_Archive/Memory-Vault/A.md",
            "top": "_Archive",
            "protected_or_archive_surface": True,
            "sha256": "same",
            "title": "A",
        },
        {
            "path": "_Archive/Only.md",
            "top": "_Archive",
            "protected_or_archive_surface": True,
            "sha256": "archive-only",
            "title": "Only",
        },
        {
            "path": "_Backups/Memory-Vault/Backup Match.md",
            "top": "_Backups",
            "sha256": "backup-same",
            "title": "Backup Match",
        },
        {
            "path": "Redirects/Canonical.md",
            "top": "Redirects",
            "canonical_path": "Memory-Vault/Canonical.md",
            "title": "Canonical",
        },
        {
            "path": "Duplicates/A Copy.md",
            "top": "Duplicates",
            "duplicate_of": "Memory-Vault/A.md",
            "title": "A",
        },
    ]


def test_archive_shadow_index_is_evidence_only_and_classifies_shadows() -> None:
    index = build_archive_shadow_index(_notes())

    assert index["mode"] == "repo-only/evidence-only"
    assert index["behavior"] == "evidence-only"
    assert index["live_mutation_authorized"] is False
    assert index["approval_manifest_created"] is False
    assert index["targets"] == []
    assert index["apply_authority"] == "none"
    assert index["reason_codes"] == [
        "active_target_available",
        "archive_shadow_only",
        "memory_plus_archive_collision",
        "redirect_collision",
        "duplicate_title_group",
    ]
    assert index["summary"]["by_kind"] == {
        "archive": 2,
        "backup": 1,
        "duplicate": 1,
        "redirect": 1,
    }


def test_active_path_hints_never_make_shadow_path_a_target() -> None:
    index = build_archive_shadow_index(_notes())
    by_shadow = {entry["shadow_path"]: entry for entry in index["entries"]}

    assert by_shadow["_Archive/Memory-Vault/A.md"]["active_path"] == "Memory-Vault/A.md"
    assert by_shadow["_Backups/Memory-Vault/Backup Match.md"]["active_path"] == (
        "Memory-Vault/Backup Match.md"
    )
    assert by_shadow["Redirects/Canonical.md"]["active_path"] == "Memory-Vault/Canonical.md"
    assert by_shadow["Duplicates/A Copy.md"]["active_path"] == "Memory-Vault/A.md"
    assert by_shadow["_Archive/Only.md"]["active_path"] is None

    for entry in index["entries"]:
        assert entry["shadow_path"] != entry["active_path"]
        assert entry["target_authority"] == "none"
        assert entry["behavior"] == "evidence-only"


def test_archive_shadow_index_writes_json_and_report_without_authorization(tmp_path) -> None:
    notes_index = tmp_path / "notes-index.jsonl"
    notes_index.write_text(
        "\n".join(json.dumps(note, sort_keys=True) for note in _notes()) + "\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "archive-shadow-index"

    result = write_archive_shadow_index(notes_index_jsonl=notes_index, out_dir=out_dir)

    index_payload = json.loads((out_dir / "archive-shadow-index.json").read_text(encoding="utf-8"))
    report = (out_dir / "REPORT.md").read_text(encoding="utf-8")

    assert result["live_mutation_authorized"] is False
    assert result["approval_manifest_created"] is False
    assert index_payload["live_mutation_authorized"] is False
    assert index_payload["approval_manifest_created"] is False
    assert index_payload["targets"] == []
    assert "live_mutation_authorized`: `false`" in report
    assert "approval_manifest_created`: `false`" in report
    assert "`targets`: `[]`" in report
