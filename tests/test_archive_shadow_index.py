from __future__ import annotations

from obslayer.archive_shadow_index import build_archive_shadow_index


def test_archive_shadow_index_classifies_collision_reason_codes() -> None:
    notes = [
        {
            "path": "Memory-Vault/A.md",
            "top": "Memory-Vault",
            "sha256": "same",
            "title": "A",
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
            "path": "Redirects/A.md",
            "top": "Redirects",
            "canonical_path": "Memory-Vault/A.md",
            "title": "A",
        },
        {
            "path": "Duplicates/A Copy.md",
            "top": "Duplicates",
            "duplicate_of": "Memory-Vault/A.md",
            "title": "A",
        },
    ]

    index = build_archive_shadow_index(notes)

    assert index["behavior"] == "evidence-only"
    assert index["live_mutation_authorized"] is False
    assert index["approval_manifest_created"] is False
    assert index["reason_codes"] == [
        "active_target_available",
        "archive_shadow_only",
        "memory_plus_archive_collision",
        "redirect_collision",
        "duplicate_title_group",
    ]
    assert index["entries"] == [
        {
            "active_path": "Memory-Vault/A.md",
            "shadow_path": "_Archive/Memory-Vault/A.md",
            "shadow_kind": "archive",
            "sha256": "same",
            "reason_codes": [
                "active_target_available",
                "memory_plus_archive_collision",
                "duplicate_title_group",
            ],
            "behavior": "evidence-only",
        },
        {
            "active_path": None,
            "shadow_path": "_Archive/Only.md",
            "shadow_kind": "archive",
            "sha256": "archive-only",
            "reason_codes": ["archive_shadow_only"],
            "behavior": "evidence-only",
        },
        {
            "active_path": "Memory-Vault/A.md",
            "shadow_path": "Duplicates/A Copy.md",
            "shadow_kind": "duplicate",
            "sha256": "",
            "reason_codes": [
                "active_target_available",
                "duplicate_title_group",
            ],
            "behavior": "evidence-only",
        },
        {
            "active_path": "Memory-Vault/A.md",
            "shadow_path": "Redirects/A.md",
            "shadow_kind": "redirect",
            "sha256": "",
            "reason_codes": [
                "active_target_available",
                "redirect_collision",
                "duplicate_title_group",
            ],
            "behavior": "evidence-only",
        },
    ]
