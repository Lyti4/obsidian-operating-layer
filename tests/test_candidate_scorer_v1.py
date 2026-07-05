from __future__ import annotations

from obslayer.candidate_scorer_v1 import score_candidate


def test_score_candidate_prefers_active_target_and_records_safety_fields() -> None:
    scored = score_candidate(
        link={
            "source": "Memory-Vault/A.md",
            "status": "ambiguous",
            "candidates": [
                "_Backups/old/Memory-Vault/B.md",
                "Memory-Vault/B.md",
            ],
        },
        notes_by_path={
            "Memory-Vault/A.md": {
                "path": "Memory-Vault/A.md",
                "top": "Memory-Vault",
                "protected_or_archive_surface": False,
            },
            "Memory-Vault/B.md": {
                "path": "Memory-Vault/B.md",
                "top": "Memory-Vault",
                "protected_or_archive_surface": False,
            },
            "_Backups/old/Memory-Vault/B.md": {
                "path": "_Backups/old/Memory-Vault/B.md",
                "top": "_Backups",
                "protected_or_archive_surface": True,
            },
        },
    )

    assert scored["behavior"] == "evidence-only"
    assert scored["live_mutation_authorized"] is False
    assert scored["approval_manifest_created"] is False
    assert scored["review_required"] is True
    assert scored["hard_stop"] is True
    assert scored["top_two_gap"] > 0
    assert "candidate_scorer_evidence_only" in scored["reason_codes"]
    assert "operator_review_required" in scored["reason_codes"]

    active = scored["candidates"][0]
    backup = scored["candidates"][1]
    assert active["path"] == "Memory-Vault/B.md"
    assert active["confidence"] > backup["confidence"]
    assert active["review_required"] is True
    assert active["hard_stop"] is False
    assert "active_target_available" in active["reason_codes"]
    assert active["safety_flags"] == ["ambiguous_link_requires_review"]
    assert active["feature_breakdown"]["candidate_archive_penalty"] == 0

    assert backup["hard_stop"] is True
    assert backup["review_required"] is True
    assert "protected_or_archive_target" in backup["reason_codes"]
    assert "backup_shadow_target" in backup["reason_codes"]
    assert "archive_or_shadow_target_hard_stop" in backup["safety_flags"]
    assert backup["feature_breakdown"]["candidate_archive_penalty"] < 0


def test_score_candidate_hard_stops_redirect_duplicate_and_missing_candidates() -> None:
    scored = score_candidate(
        link={
            "source": "Memory-Vault/A.md",
            "status": "ambiguous",
            "candidates": [
                "Redirects/B.md",
                "Duplicates/B copy.md",
                "Memory-Vault/Missing.md",
            ],
        },
        notes_by_path={
            "Memory-Vault/A.md": {
                "path": "Memory-Vault/A.md",
                "top": "Memory-Vault",
                "protected_or_archive_surface": False,
            },
            "Redirects/B.md": {
                "path": "Redirects/B.md",
                "top": "Redirects",
                "canonical_path": "Memory-Vault/B.md",
            },
            "Duplicates/B copy.md": {
                "path": "Duplicates/B copy.md",
                "top": "Duplicates",
                "duplicate_of": "Memory-Vault/B.md",
            },
        },
    )

    by_path = {item["path"]: item for item in scored["candidates"]}
    assert scored["review_required"] is True
    assert scored["hard_stop"] is True
    assert scored["top_two_gap"] >= 0

    assert "redirect_shadow_target" in by_path["Redirects/B.md"]["reason_codes"]
    assert by_path["Redirects/B.md"]["hard_stop"] is True
    assert "canonical_shadow_target" in by_path["Redirects/B.md"]["reason_codes"]

    assert "duplicate_shadow_target" in by_path["Duplicates/B copy.md"]["reason_codes"]
    assert by_path["Duplicates/B copy.md"]["hard_stop"] is True

    assert "candidate_missing_from_index" in by_path["Memory-Vault/Missing.md"]["reason_codes"]
    assert by_path["Memory-Vault/Missing.md"]["review_required"] is True
    assert by_path["Memory-Vault/Missing.md"]["hard_stop"] is True
