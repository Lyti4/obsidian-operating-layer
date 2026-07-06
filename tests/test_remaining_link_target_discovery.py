from __future__ import annotations

from obslayer.remaining_link_target_discovery import build_target_discovery_packet, discover_target_for_item


def test_suppressed_policy_items_do_not_become_proposals() -> None:
    item = discover_target_for_item(
        {
            "source": "Hermes/Report.md",
            "raw": "Missing",
            "target": "Missing",
            "status": "broken",
            "classification": "generated_report_auto_keep",
        },
        notes=[{"path": "Hermes/Missing.md", "title": "Missing"}],
    )

    assert item.decision == "suppressed_by_policy"
    assert item.apply_authority == "none"
    assert item.live_mutation_authorized is False
    assert item.approval_manifest_created is False
    assert item.proposed_new_link is None


def test_high_confidence_discovery_is_proposal_only() -> None:
    item = discover_target_for_item(
        {
            "source": "Hermes/Source.md",
            "raw": "Target Note|alias",
            "target": "Target Note",
            "status": "broken",
            "classification": "real_broken_needs_target_discovery",
        },
        notes=[{"path": "Hermes/Target Note.md", "title": "Target Note"}],
    )

    assert item.decision == "proposal_candidate"
    assert item.proposed_new_link == "Hermes/Target Note|alias"
    assert item.apply_authority == "none"
    assert item.live_mutation_authorized is False
    assert item.approval_manifest_created is False


def test_tied_discovery_requires_manual_review() -> None:
    item = discover_target_for_item(
        {
            "source": "Hermes/Source.md",
            "raw": "Target Note",
            "target": "Target Note",
            "status": "ambiguous",
            "classification": "ambiguous_needs_operator_disambiguation",
        },
        notes=[
            {"path": "Hermes/Target Note.md", "title": "Target Note"},
            {"path": "Other/Target Note.md", "title": "Target Note"},
        ],
    )

    assert item.decision == "manual_review_required"
    assert item.proposed_new_link is None


def test_packet_current_safety_fields_are_closed() -> None:
    packet = build_target_discovery_packet(
        triage_packet={
            "items": [
                {
                    "source": "Hermes/Report.md",
                    "raw": "Missing",
                    "target": "Missing",
                    "status": "broken",
                    "classification": "generated_report_auto_keep",
                }
            ]
        },
        notes_index=[{"path": "Hermes/Missing.md", "title": "Missing"}],
    )

    assert packet["status"] == "no_live_candidates"
    assert packet["apply_authority"] == "none"
    assert packet["live_mutation_authorized"] is False
    assert packet["approval_manifest_created"] is False
    assert packet["summary"]["proposal_candidates"] == 0


def test_safety_flagged_candidate_requires_manual_review() -> None:
    item = discover_target_for_item(
        {
            "source": "Hermes/Source.md",
            "raw": "Target Note",
            "target": "Target Note",
            "status": "broken",
            "classification": "real_broken_needs_target_discovery",
        },
        notes=[{"path": "_Archive/Target Note.md", "title": "Target Note"}],
    )

    assert item.decision == "manual_review_required"
    assert item.candidates[0].safety_flags == ["protected_path"]
    assert item.proposed_new_link is None


def test_target_discovery_promotes_same_source_vault_exact_over_protected_mirror() -> None:
    packet = build_target_discovery_packet(
        triage_packet={
            "items": [
                {
                    "source": "Memory-Vault/00 Memory Graph Index.md",
                    "raw": "Hermes/Browser Tooling Research",
                    "target": "Hermes/Browser Tooling Research",
                    "status": "ambiguous",
                    "classification": "ambiguous_needs_operator_disambiguation",
                }
            ]
        },
        notes_index=[
            {"path": "Memory-Vault/Hermes/Browser Tooling Research.md", "title": "Browser Tooling Research"},
            {"path": "Soul-Vault/Hermes/Browser Tooling Research.md", "title": "Browser Tooling Research"},
        ],
    )
    item = packet["items"][0]
    assert item["decision"] == "proposal_candidate"
    assert item["proposed_new_link"] == "Memory-Vault/Hermes/Browser Tooling Research"


def test_target_discovery_does_not_promote_protected_source_same_vault_exact() -> None:
    packet = build_target_discovery_packet(
        triage_packet={
            "items": [
                {
                    "source": "Soul-Vault/Hermes/Soul Organism Kanban.md",
                    "raw": "Hermes/00 Hermes Index",
                    "target": "Hermes/00 Hermes Index",
                    "status": "ambiguous",
                    "classification": "ambiguous_needs_operator_disambiguation",
                }
            ]
        },
        notes_index=[{"path": "Soul-Vault/Hermes/00 Hermes Index.md", "title": "00 Hermes Index"}],
    )
    assert packet["items"][0]["decision"] == "manual_review_required"


def test_target_discovery_flags_protected_vault_candidate() -> None:
    packet = build_target_discovery_packet(
        triage_packet={
            "items": [
                {
                    "source": "Memory-Vault/Hermes/A.md",
                    "raw": "Hermes/Only In Soul",
                    "target": "Hermes/Only In Soul",
                    "status": "broken",
                    "classification": "real_broken_needs_target_discovery",
                }
            ]
        },
        notes_index=[{"path": "Soul-Vault/Hermes/Only In Soul.md", "title": "Only In Soul"}],
    )
    item = packet["items"][0]
    assert item["decision"] == "manual_review_required"
    assert "protected_vault_root" in item["candidates"][0]["safety_flags"]
