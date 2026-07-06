from __future__ import annotations

import json
from pathlib import Path

import obslayer.manual_review_selector_v1 as manual_review_selector_v1
from obslayer.external_autograph_policy import load_external_autograph_policy, validate_external_autograph_policy
from obslayer.manual_review_selector_v1 import (
    build_manual_review_selector_packet,
    classify_alias_review_item,
    classify_alias_review_packet,
    manual_review_selector_to_markdown,
    write_manual_review_selector_packet,
)


def test_build_manual_review_selector_ranks_active_memory_matches() -> None:
    packet = {
        "schema": "obslayer.candidate-scorer.v1",
        "status": "ok",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "apply_authority": "none",
        "targets": [],
        "scored_links": [
            {
                "source": "Memory-Vault/Foo.md",
                "old_link": "[[Alpha]]",
                "route_hint": "needs-human-review",
                "top_two_gap": 40,
                "reason_codes": ["active_target_available"],
                "candidates": [
                    {
                        "path": "Memory-Vault/Notes/Alpha.md",
                        "score": 84,
                        "confidence": 0.98,
                        "reason_codes": ["exact_title_match", "active_target_available"],
                    }
                ],
            },
            {
                "source": "Notes/Archive.md",
                "old_link": "[[Beta]]",
                "route_hint": "needs-human-review",
                "top_two_gap": 15,
                "reason_codes": ["active_target_available"],
                "candidates": [
                    {
                        "path": "_Archive/Beta.md",
                        "score": 95,
                        "confidence": 0.99,
                        "reason_codes": ["exact_title_match"],
                    }
                ],
            },
        ],
    }

    result = build_manual_review_selector_packet(packet, max_candidates=2)

    assert result["status"] == "ready_for_manual_review"
    assert len(result["review_items"]) == 1
    item = result["review_items"][0]
    assert item["source"] == "Memory-Vault/Foo.md"
    assert item["proposed_path"] == "Memory-Vault/Notes/Alpha.md"
    assert item["policy_tag"] == "manual-review-only"
    assert "exact_title_match" in item["reason_codes"]
    assert "active_target_available" in item["reason_codes"]
    assert result["summary"]["review_items"] == 1


def test_safe_auto_packet_is_enriched_from_source_candidate_packet(tmp_path: Path) -> None:
    source_packet = {
        "schema": "obslayer.candidate-scorer.v1",
        "status": "ok",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "apply_authority": "none",
        "targets": [],
        "scored_links": [
            {
                "source": "Evidence/Root.md",
                "old_link": "[[Gamma]]",
                "route_hint": "needs-human-review",
                "top_two_gap": 20,
                "candidates": [
                    {
                        "path": "Memory-Vault/Gamma.md",
                        "score": 90,
                        "confidence": 0.93,
                        "reason_codes": ["alias_match", "active_target_available"],
                    }
                ],
            }
        ],
    }
    source_path = tmp_path / "candidate-scorer-v1.json"
    source_path.write_text(__import__("json").dumps(source_packet), encoding="utf-8")

    safe_auto_packet = {
        "schema": "obslayer.safe-auto-proposal-thresholds.v1",
        "status": "ok",
        "source_candidate_scorer_packet": str(source_path),
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "apply_authority": "none",
        "targets": [],
        "held_for_review": [
            {
                "source": "Evidence/Root.md",
                "old_link": "[[Gamma]]",
                "route_hint": "suggest",
                "reason_codes": ["active_target_available", "exact_title_match"],
            }
        ],
    }

    result = build_manual_review_selector_packet(safe_auto_packet)

    assert result["status"] == "ready_for_manual_review"
    item = result["review_items"][0]
    assert item["proposed_path"] == "Memory-Vault/Gamma.md"
    assert "manual-review-only" in item["policy_tag"]


def test_safe_auto_packet_is_enriched_from_source_candidate_packet_id(tmp_path: Path) -> None:
    reports_root = tmp_path / "out" / "reports"

    source_packet = {
        "schema": "obslayer.candidate-scorer.v1",
        "status": "ok",
        "packet_id": "candidate-scorer-v1-20260705T175815Z",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "apply_authority": "none",
        "targets": [],
        "scored_links": [
            {
                "source": "Evidence/Delta.md",
                "old_link": "[[Delta]]",
                "route_hint": "needs-human-review",
                "top_two_gap": 18,
                "candidates": [
                    {
                        "path": "Memory-Vault/Delta.md",
                        "score": 88,
                        "confidence": 0.94,
                        "reason_codes": ["alias_match", "active_target_available"],
                    }
                ],
            }
        ],
    }

    source_root = reports_root / "candidate-scorer-v1" / "candidate-scorer-v1-20260705T175815Z"
    source_root.mkdir(parents=True)
    (source_root / "candidate-scorer-v1.json").write_text(
        json.dumps(source_packet),
        encoding="utf-8",
    )

    safe_auto_root = reports_root / "safe-auto-proposal-thresholds-v1" / "safe-auto-proposal-thresholds-v1-20260705T175816Z"
    safe_auto_root.mkdir(parents=True)
    safe_auto_packet_path = safe_auto_root / "safe-auto-proposal-thresholds-v1.json"
    safe_auto_packet = {
        "schema": "obslayer.safe-auto-proposal-thresholds.v1",
        "status": "ok",
        "source_candidate_scorer_packet": "candidate-scorer-v1-20260705T175815Z",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "apply_authority": "none",
        "targets": [],
        "held_for_review": [
            {
                "source": "Evidence/Delta.md",
                "old_link": "[[Delta]]",
                "route_hint": "needs-human-review",
                "reason_codes": ["active_target_available", "exact_title_match"],
            }
        ],
    }
    safe_auto_packet_path.write_text(json.dumps(safe_auto_packet), encoding="utf-8")

    result = build_manual_review_selector_packet(
        safe_auto_packet,
        proposal_packet_path=str(safe_auto_packet_path),
    )

    assert result["status"] == "ready_for_manual_review"
    item = result["review_items"][0]
    assert item["proposed_path"] == "Memory-Vault/Delta.md"
    assert result["summary"]["selection_diagnostics"]["forbidden_path"]["total"] == 0
    assert result["summary"]["selection_diagnostics"]["selected"] == 1


def test_blocked_refuse_is_salvaged_for_manual_review_when_top_candidate_is_safe() -> None:
    packet = {
        "schema": "obslayer.candidate-scorer.v1",
        "status": "ok",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "apply_authority": "none",
        "targets": [],
        "scored_links": [
            {
                "source": "Memory-Vault/Hermes/Source.md",
                "old_link": "Memory-Vault/Hermes/Target|Target",
                "route_hint": "blocked/refuse",
                "hard_stop": True,
                "top_two_gap": 134,
                "reason_codes": [
                    "candidate_scorer_evidence_only",
                    "active_target_available",
                    "exact_path_match",
                    "exact_title_match",
                    "protected_or_archive_target",
                    "unsafe_candidate_hard_stop",
                ],
                "safety_flags": [
                    "ambiguous_link_requires_review",
                    "archive_or_shadow_target_hard_stop",
                    "hard_stop_candidate_present",
                ],
                "candidates": [
                    {
                        "path": "Memory-Vault/Hermes/Target.md",
                        "score": 136,
                        "confidence": 1.0,
                        "hard_stop": False,
                        "reason_codes": [
                            "active_target_available",
                            "exact_path_match",
                            "exact_title_match",
                            "same_top_level",
                        ],
                        "safety_flags": ["ambiguous_link_requires_review"],
                    },
                    {
                        "path": "_Backups/Hermes/Target.md",
                        "score": 2,
                        "confidence": 0.02,
                        "hard_stop": True,
                        "reason_codes": ["backup_shadow_target", "protected_or_archive_target"],
                        "safety_flags": ["archive_or_shadow_target_hard_stop"],
                    },
                ],
            }
        ],
    }

    result = build_manual_review_selector_packet(packet)

    assert result["status"] == "ready_for_manual_review"
    assert result["summary"]["selection_diagnostics"]["blocked_refuse_salvaged"] == 1
    item = result["review_items"][0]
    assert item["selection_mode"] == "blocked_refuse_salvage"
    assert item["proposed_path"] == "Memory-Vault/Hermes/Target.md"
    assert item["unsafe_lower_ranked_candidates_count"] == 1
    assert item["blocked_refuse_salvage_reason"] == "top_active_exact_candidate_lower_ranked_shadow_candidates_only"
    assert result["apply_authority"] == "none"


def test_blocked_refuse_salvage_rejects_low_gap_and_records_sample() -> None:
    packet = {
        "schema": "obslayer.candidate-scorer.v1",
        "status": "ok",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "apply_authority": "none",
        "targets": [],
        "scored_links": [
            {
                "source": "Memory-Vault/Hermes/Source.md",
                "old_link": "Memory-Vault/Hermes/Target|Target",
                "route_hint": "blocked/refuse",
                "hard_stop": True,
                "top_two_gap": 10,
                "candidates": [
                    {
                        "path": "Memory-Vault/Hermes/Target.md",
                        "score": 136,
                        "confidence": 1.0,
                        "hard_stop": False,
                        "reason_codes": ["active_target_available", "exact_title_match"],
                        "safety_flags": ["ambiguous_link_requires_review"],
                    },
                    {
                        "path": "_Backups/Hermes/Target.md",
                        "hard_stop": True,
                        "reason_codes": ["backup_shadow_target"],
                    },
                ],
            }
        ],
    }

    result = build_manual_review_selector_packet(packet)

    assert result["status"] == "no_candidate"
    diagnostics = result["summary"]["selection_diagnostics"]
    assert diagnostics["blocked_refuse_rejected"]["reasons"] == {"top_two_gap_too_small": 1}
    assert diagnostics["rejected_samples"][0]["reason"] == "top_two_gap_too_small"


def test_blocked_if_unsafe_authority_flags_present() -> None:
    packet = {
        "schema": "obslayer.candidate-scorer.v1",
        "status": "ok",
        "live_mutation_authorized": True,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "apply_authority": "none",
        "targets": [],
        "scored_links": [],
    }
    result = build_manual_review_selector_packet(packet)

    assert result["status"] == "blocked"
    assert "live_mutation_authorized must be false" in result["findings"]


def test_no_candidate_when_none_selected(tmp_path: Path) -> None:
    packet = {
        "schema": "obslayer.candidate-scorer.v1",
        "status": "ok",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "apply_authority": "none",
        "targets": [],
        "scored_links": [
            {
                "source": "Evidence/Root.md",
                "old_link": "[[Nope]]",
                "route_hint": "auto-propose",
                "candidates": [
                    {
                        "path": "Memory-Vault/Nope.md",
                        "score": 99,
                        "confidence": 0.99,
                        "reason_codes": ["high_confidence"],
                    }
                ],
            }
        ],
    }
    result = build_manual_review_selector_packet(packet)

    assert result["status"] == "no_candidate"
    assert result["review_items"] == []
    assert manual_review_selector_to_markdown(result).startswith("# Manual Review Selector")


def test_cli_writer_writes_payloads(tmp_path: Path) -> None:
    packet = {
        "schema": "obslayer.candidate-scorer.v1",
        "status": "ok",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "apply_authority": "none",
        "targets": [],
        "scored_links": [
            {
                "source": "Memory-Vault/Foo.md",
                "old_link": "[[Item]]",
                "route_hint": "needs-human-review",
                "candidates": [
                    {
                        "path": "Memory-Vault/Item.md",
                        "score": 80,
                        "confidence": 0.9,
                        "reason_codes": ["exact_title_match", "active_target_available"],
                    }
                ],
            }
        ],
    }
    proposal_path = tmp_path / "packet.json"
    proposal_path.write_text(__import__("json").dumps(packet), encoding="utf-8")

    out = tmp_path / "out"
    artifact = write_manual_review_selector_packet(
        proposal_packet=proposal_path,
        out_dir=out,
        max_candidates=1,
    )

    assert artifact["status"] == "ready_for_manual_review"
    assert (out / "manual-review-selector-v1.json").exists()
    assert (out / "manual-review-items.jsonl").exists()
    assert (out / "REPORT.md").exists()


def test_cli_writer_resolves_source_candidate_scorer_by_id_with_proposal_path(tmp_path: Path) -> None:
    source_packet = {
        "schema": "obslayer.candidate-scorer.v1",
        "status": "ok",
        "packet_id": "candidate-scorer-v1-999999T999999Z",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "apply_authority": "none",
        "targets": [],
        "scored_links": [
            {
                "source": "Evidence/Omega.md",
                "old_link": "[[Omega]]",
                "route_hint": "needs-human-review",
                "top_two_gap": 25,
                "candidates": [
                    {
                        "path": "Memory-Vault/Omega.md",
                        "score": 92,
                        "confidence": 0.96,
                        "reason_codes": ["alias_match", "active_target_available"],
                    }
                ],
            }
        ],
    }

    source_root = tmp_path / "out" / "reports" / "candidate-scorer-v1" / "candidate-scorer-v1-999999T999999Z"
    source_root.mkdir(parents=True)
    (source_root / "candidate-scorer-v1.json").write_text(json.dumps(source_packet), encoding="utf-8")

    safe_root = tmp_path / "out" / "reports" / "safe-auto-proposal-thresholds-v1" / "safe-auto-proposal-thresholds-v1-888888T888888Z"
    safe_root.mkdir(parents=True)
    safe_packet_path = safe_root / "safe-auto-proposal-thresholds-v1.json"
    safe_packet = {
        "schema": "obslayer.safe-auto-proposal-thresholds.v1",
        "status": "ok",
        "source_candidate_scorer_packet": "candidate-scorer-v1-999999T999999Z",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "apply_authority": "none",
        "targets": [],
        "held_for_review": [
            {
                "source": "Evidence/Omega.md",
                "old_link": "[[Omega]]",
                "route_hint": "needs-human-review",
                "reason_codes": ["active_target_available", "exact_title_match"],
            }
        ],
    }
    safe_packet_path.write_text(json.dumps(safe_packet), encoding="utf-8")

    out = tmp_path / "out-manual"
    artifact = manual_review_selector_v1.write_manual_review_selector_packet(
        proposal_packet=safe_packet_path,
        out_dir=out,
        max_candidates=1,
    )

    assert artifact["status"] == "ready_for_manual_review"
    selector = manual_review_selector_v1.load_json(artifact["packet"])
    assert selector["summary"]["selected"] == 1
    assert selector["review_items"][0]["proposed_path"] == "Memory-Vault/Omega.md"


def test_blocked_refuse_salvage_preserves_taxonomy_provenance_and_batching() -> None:
    packet = {
        "schema": "obslayer.candidate-scorer.v1",
        "status": "ok",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "apply_authority": "none",
        "targets": [],
        "scored_links": [
            {
                "source": "Memory-Vault/Hermes/Source.md",
                "old_link": "[[Target]]",
                "route_hint": "blocked/refuse",
                "hard_stop": True,
                "top_two_gap": 90,
                "reason_codes": ["protected_or_archive_target", "unsafe_candidate_hard_stop"],
                "safety_flags": ["hard_stop_candidate_present"],
                "candidates": [
                    {
                        "path": "Memory-Vault/Hermes/Target.md",
                        "score": 120,
                        "confidence": 0.91,
                        "hard_stop": False,
                        "reason_codes": ["active_target_available", "exact_title_match"],
                        "safety_flags": ["ambiguous_link_requires_review"],
                    }
                ],
            }
        ],
    }

    result = build_manual_review_selector_packet(packet)

    assert result["status"] == "ready_for_manual_review"
    item = result["review_items"][0]
    assert item["policy_tag"] == "manual-review-only"
    assert item["policy_taxonomy"] | {
        "source_policy": item["policy_taxonomy"]["source_policy"],
        "classification": item["policy_taxonomy"]["classification"],
        "risk": item["policy_taxonomy"]["risk"],
    } == item["policy_taxonomy"]
    assert item["policy_taxonomy"]["schema"] == "obslayer.manual-review-selector.v1"
    assert item["policy_taxonomy"]["packet_type"] == "manual_review_evidence_only"
    assert item["policy_taxonomy"]["authority"] == "manual-review-only"
    assert item["policy_taxonomy"]["route_class"] == "salvaged_blocked_refuse"
    assert item["policy_taxonomy"]["decision_class"] == "soft_salvage_candidate"
    assert item["policy_taxonomy"]["apply_authority"] == "none"
    assert item["policy_taxonomy"]["source_policy"]["policy_ref"] == "docs/spec-kit/44-external-autograph-policy-adapter.md"
    assert item["policy_taxonomy"]["classification"] == "blocked_refuse_salvage_manual_review"
    assert item["policy_taxonomy"]["risk"] == "medium"
    assert item["candidate_count"] == 1
    assert item["top_score"] == 120
    assert item["blocked_refuse_salvage_reason"] == "top_active_exact_candidate_single_candidate_manual_review_only"
    assert item["source_provenance"]["hard_stop"] is True
    assert item["source_provenance"]["reason_codes"] == ["protected_or_archive_target", "unsafe_candidate_hard_stop"]
    assert item["source_provenance"]["safety_flags"] == ["hard_stop_candidate_present"]
    assert item["thresholds"] == {"salvage_min_score": 80, "salvage_min_top_two_gap": 40}
    assert result["summary"]["selection_contract"]["authority"] == "manual-review-only"
    assert result["summary"]["batching"]["accepted_total"] == 1
    assert result["summary"]["batching"]["recommended_initial_sample_size"] == 1


def test_blocked_refuse_rejects_hard_top_candidate_and_classifies_reason() -> None:
    packet = {
        "schema": "obslayer.candidate-scorer.v1",
        "status": "ok",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "apply_authority": "none",
        "targets": [],
        "scored_links": [
            {
                "source": "Memory-Vault/Hermes/Source.md",
                "old_link": "[[Target]]",
                "route_hint": "blocked/refuse",
                "hard_stop": True,
                "top_two_gap": 90,
                "candidates": [
                    {
                        "path": "Memory-Vault/Hermes/Target.md",
                        "score": 120,
                        "confidence": 0.91,
                        "hard_stop": True,
                        "reason_codes": ["active_target_available", "exact_title_match"],
                    }
                ],
            }
        ],
    }

    result = build_manual_review_selector_packet(packet)

    diagnostics = result["summary"]["selection_diagnostics"]["blocked_refuse_rejected"]
    assert result["status"] == "no_candidate"
    assert diagnostics["reasons"] == {"top_candidate_hard_stop": 1}
    assert diagnostics["hard_reject"] == {"top_candidate_hard_stop": 1}
    assert diagnostics["soft_reject"] == {}
    sample = result["summary"]["selection_diagnostics"]["rejected_samples"][0]
    assert sample["rejection_category"] == "hard"
    assert sample["policy_tag"] == "manual-review-only"


def test_blocked_refuse_salvage_emits_review_only_schema_and_queue_metadata() -> None:
    packet = {
        "schema": "obslayer.candidate-scorer.v1",
        "status": "ok",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "apply_authority": "none",
        "targets": [],
        "scored_links": [
            {
                "source": "Memory-Vault/Hermes/Source.md",
                "old_link": "[[Target]]",
                "route_hint": "blocked/refuse",
                "hard_stop": True,
                "top_two_gap": 90,
                "reason_codes": ["protected_or_archive_target", "unsafe_candidate_hard_stop"],
                "safety_flags": ["hard_stop_candidate_present"],
                "candidates": [
                    {
                        "path": "Memory-Vault/Hermes/Target.md",
                        "score": 120,
                        "confidence": 0.91,
                        "hard_stop": False,
                        "reason_codes": ["active_target_available", "exact_title_match"],
                        "safety_flags": ["ambiguous_link_requires_review"],
                    }
                ],
            }
        ],
    }

    result = build_manual_review_selector_packet(packet)

    assert result["schema"] == "obslayer.manual-review-selector.v1"
    assert result["packet_type"] == "manual_review_evidence_only"
    assert result["manual_review_only"] is True
    assert result["live_mutation_allowed"] is False
    assert result["approval_manifest"] is None
    assert result["requires_explicit_approval_before_apply"] is True
    item = result["review_items"][0]
    assert item["manual_review_only"] is True
    assert item["approval_manifest_id"] is None
    assert item["proposed_action"] == "review_only"
    assert item["review_queue"]["batch_id"] == "manual-review-only-0001"
    assert item["review_queue"]["batch_index"] == 1
    assert item["review_queue"]["item_index_in_batch"] == 0
    assert item["review_queue"]["item_id"].startswith("manual-review-only-")


def test_blocked_refuse_rejects_hard_deny_source_path_reason_and_safety_flags() -> None:
    cases = [
        ("source_forbidden_surface", {"source": "Memory-Vault/Hermes/Soul/Source.md"}, {}),
        ("top_candidate_forbidden_path", {}, {"path": "_Archive/Target.md"}),
        (
            "top_candidate_forbidden_safety_flag",
            {},
            {"safety_flags": ["ambiguous_link_requires_review", "soul_policy_sensitive"]},
        ),
        (
            "top_candidate_forbidden_reason_code",
            {},
            {"reason_codes": ["active_target_available", "exact_title_match", "target_soul_surface"]},
        ),
    ]

    for expected_reason, link_overrides, top_overrides in cases:
        top_candidate = {
            "path": "Memory-Vault/Hermes/Target.md",
            "score": 120,
            "confidence": 0.91,
            "hard_stop": False,
            "reason_codes": ["active_target_available", "exact_title_match"],
            "safety_flags": ["ambiguous_link_requires_review"],
        }
        top_candidate.update(top_overrides)
        packet = {
            "schema": "obslayer.candidate-scorer.v1",
            "status": "ok",
            "live_mutation_authorized": False,
            "approval_manifest_created": False,
            "approval_manifest_authority": False,
            "apply_authority": "none",
            "targets": [],
            "scored_links": [
                {
                    "source": "Memory-Vault/Hermes/Source.md",
                    "old_link": "[[Target]]",
                    "route_hint": "blocked/refuse",
                    "hard_stop": True,
                    "top_two_gap": 90,
                    "candidates": [top_candidate],
                    **link_overrides,
                }
            ],
        }

        result = build_manual_review_selector_packet(packet)

        diagnostics = result["summary"]["selection_diagnostics"]["blocked_refuse_rejected"]
        assert result["status"] == "no_candidate"
        assert diagnostics["reasons"] == {expected_reason: 1}
        assert diagnostics["hard_reject"] == {expected_reason: 1}
        assert diagnostics["soft_reject"] == {}

def test_alias_policy_classifier_keeps_generated_heading_anchor_aliases() -> None:
    item = {
        "rel_file": "Hermes/Reports/graphify-spark-corpus-c10-2026-06-27/GRAPH_REPORT.md",
        "target": '#Community 0 - "Community 0"',
        "alias": "Community 0",
        "reason": "target_file_missing_or_unresolved",
        "target_file_exists": False,
    }

    classification = classify_alias_review_item(item)

    assert classification["decision"] == "keep_alias_no_apply"
    assert classification["policy_class"] == "heading_anchor_alias_keep"
    assert classification["user_decision_required"] is False
    assert "docs/spec-kit/38-generated-report-noise-policy.md" in classification["policy_refs"]


def test_alias_policy_classifier_keeps_semantic_short_aliases() -> None:
    item = {
        "rel_file": "Hermes/HERMES_HOME.md",
        "target": "Hermes/Reports/graphify-small-workers-dry-run-2026-06-27",
        "target_basename": "graphify-small-workers-dry-run-2026-06-27",
        "alias": "Small-workers dry-run",
        "reason": "contained_title_variant",
        "target_file_exists": True,
    }

    classification = classify_alias_review_item(item)

    assert classification["decision"] == "keep_alias_no_apply"
    assert classification["policy_class"] in {"generated_report_alias_keep", "semantic_short_alias_keep"}
    assert classification["user_decision_required"] is False


def test_alias_policy_classifier_keeps_protected_cross_vault_aliases_manual_only() -> None:
    item = {
        "rel_file": "Hermes/Report.md",
        "target": "Hermes/Soul/Personality",
        "alias": "Soul policy",
        "reason": "target_file_missing_or_unresolved",
        "target_file_exists": False,
    }

    classification = classify_alias_review_item(item)

    assert classification["decision"] == "manual_only_no_apply"
    assert classification["policy_class"] == "protected_or_cross_vault_manual"
    assert classification["user_decision_required"] is False
    assert "docs/spec-kit/39-protected-cross-vault-link-policy.md" in classification["policy_refs"]


def test_alias_policy_classifier_marks_normalized_title_as_safe_candidate_without_authority() -> None:
    item = {
        "rel_file": "Hermes/Graphify Latest.md",
        "target": "Hermes/Obsidian cleanup next queue 2026-06-27",
        "target_basename": "Obsidian cleanup next queue 2026-06-27",
        "alias": "Obsidian cleanup next queue",
        "reason": "normalized_title_match",
        "bucket": "safe_candidate_review_first",
        "target_file_exists": True,
    }

    classification = classify_alias_review_item(item)

    assert classification["decision"] == "safe_apply_candidate"
    assert classification["live_apply_authorized"] is False
    assert classification["apply_authority"] == "none"


def test_alias_policy_classifier_keeps_generated_normalized_report_aliases() -> None:
    item = {
        "rel_file": "Hermes/Graphify Latest.md",
        "target": "Hermes/Reports/obsidian-cleanup-next-queue-2026-06-27",
        "target_basename": "obsidian-cleanup-next-queue-2026-06-27",
        "alias": "Obsidian cleanup next queue",
        "reason": "normalized_title_match",
        "bucket": "safe_candidate_review_first",
        "target_file_exists": True,
    }

    classification = classify_alias_review_item(item)

    assert classification["decision"] == "keep_alias_no_apply"
    assert classification["policy_class"] == "generated_report_alias_keep"
    assert classification["user_decision_required"] is False
    assert "docs/spec-kit/38-generated-report-noise-policy.md" in classification["policy_refs"]


def test_alias_policy_classifier_preserves_operator_keep_no_apply_decision() -> None:
    item = {
        "rel_file": "Hermes/HERMES_HOME.md",
        "target": "Hermes/Hermes Loop Engineering and Forked Context MOC",
        "target_basename": "Hermes Loop Engineering and Forked Context MOC",
        "alias": "Loop Engineering",
        "reason": "contained_title_variant",
        "bucket": "needs_human_review",
        "target_file_exists": True,
        "operator_decision": "keep_alias_no_apply",
        "user_required": False,
    }

    classification = classify_alias_review_item(item)

    assert classification["decision"] == "keep_alias_no_apply"
    assert classification["policy_class"] == "operator_review_keep_alias_no_apply"
    assert classification["user_decision_required"] is False
    assert "docs/spec-kit/42-operator-review-packet.md" in classification["policy_refs"]


def test_alias_policy_packet_summary_counts_user_decisions() -> None:
    packet = {
        "schema": "obslayer_broad_alias_review_packet.v1",
        "items": [
            {"target": "#H", "alias": "H", "reason": "target_file_missing_or_unresolved"},
            {"target": "Notes/Foo", "alias": "Bar", "reason": "unknown", "target_file_exists": True},
        ],
    }

    classified = classify_alias_review_packet(packet)

    assert classified["summary"]["decisions"]["keep_alias_no_apply"] == 1
    assert classified["summary"]["decisions"]["needs_operator_review"] == 1
    assert classified["summary"]["user_decision_required"] == 1
    assert classified["live_mutation_authorized"] is False


def test_selector_item_exposes_external_policy_metadata_for_safe_link_candidate() -> None:
    packet = {
        "schema": "obslayer.candidate-scorer.v1",
        "status": "ok",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "apply_authority": "none",
        "targets": [],
        "scored_links": [
            {
                "source": "Memory-Vault/Foo.md",
                "old_link": "[[Alpha]]",
                "route_hint": "needs-human-review",
                "top_two_gap": 50,
                "candidates": [
                    {
                        "path": "Memory-Vault/Alpha.md",
                        "score": 90,
                        "confidence": 0.99,
                        "reason_codes": ["active_target_available", "exact_title_match"],
                    }
                ],
            }
        ],
    }

    result = build_manual_review_selector_packet(packet)

    item = result["review_items"][0]
    assert item["source_policy"]["policy_id"] == "external-autograph-policy-adapter.v1"
    assert item["source_policy"]["policy_ref"] == "docs/spec-kit/44-external-autograph-policy-adapter.md"
    assert item["source_policy"]["rule_id"] == "link-resolution-exact-or-unique"
    assert item["classification"] == "link_resolution_safe_candidate"
    assert item["risk"] == "low"
    assert item["apply_authority"] == "none"
    contract = result["summary"]["selection_contract"]
    assert contract["manifest_approval_contract"]["approved_default"] is False
    assert contract["dedup_action_taxonomy"]["manual_hold"]["risk"] == "high"
    assert contract["dedup_action_taxonomy"]["merge_duplicate"]["approved_default"] is False


def test_selector_denylist_rejects_generated_report_noise_targets() -> None:
    packet = {
        "schema": "obslayer.candidate-scorer.v1",
        "status": "ok",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "apply_authority": "none",
        "targets": [],
        "scored_links": [
            {
                "source": "Memory-Vault/Foo.md",
                "old_link": "[[Graph Report]]",
                "route_hint": "needs-human-review",
                "candidates": [
                    {
                        "path": "out/reports/graphify/GRAPH_REPORT.md",
                        "score": 99,
                        "confidence": 0.99,
                        "reason_codes": ["active_target_available", "exact_title_match"],
                    }
                ],
            }
        ],
    }

    result = build_manual_review_selector_packet(packet)

    assert result["status"] == "no_candidate"
    assert result["summary"]["selection_diagnostics"]["forbidden_path"]["total"] == 1
    contract = result["summary"]["selection_contract"]
    assert "out/reports/" in contract["generated_report_noise_denylist"]["path_parts"]


def test_alias_classification_exposes_policy_source_risk_and_authority() -> None:
    classification = classify_alias_review_item(
        {
            "rel_file": "Hermes/Report.md",
            "target": "Hermes/Soul/Personality",
            "alias": "Soul policy",
            "reason": "target_file_missing_or_unresolved",
            "target_file_exists": False,
        }
    )

    assert classification["source_policy"]["policy_ref"] == "docs/spec-kit/44-external-autograph-policy-adapter.md"
    assert classification["classification"] == "protected_or_cross_vault_manual"
    assert classification["risk"] == "high"
    assert classification["apply_authority"] == "none"



def test_external_autograph_policy_artifact_is_machine_readable_and_safe_by_default() -> None:
    policy = load_external_autograph_policy()

    validate_external_autograph_policy(policy)
    assert policy["policy_id"] == "external-autograph-policy-adapter.v1"
    assert policy["authority"]["default_apply_authority"] == "none"
    assert policy["authority"]["live_mutation_authorized"] is False
    assert policy["authority"]["approved_default"] is False
    assert "_Archive/" in policy["protected_path_denylist"]
    assert "out/reports/" in policy["generated_report_noise"]["path_parts"]
    assert policy["dedup_action_taxonomy"]["merge_duplicate"]["approved_default"] is False


def test_selector_contract_is_sourced_from_external_policy_artifact() -> None:
    policy = load_external_autograph_policy()
    packet = {
        "schema": "obslayer.candidate-scorer.v1",
        "status": "ok",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "apply_authority": "none",
        "targets": [],
        "scored_links": [],
    }

    result = build_manual_review_selector_packet(packet)

    contract = result["summary"]["selection_contract"]
    assert contract["source_policy"]["policy_id"] == policy["policy_id"]
    assert contract["protected_path_denylist"] == policy["protected_path_denylist"]
    assert contract["generated_report_noise_denylist"]["path_parts"] == policy["generated_report_noise"]["path_parts"]
    assert contract["generated_report_noise_denylist"]["noise_words"] == policy["generated_report_noise"]["noise_words"]
    assert contract["dedup_action_taxonomy"] == policy["dedup_action_taxonomy"]
