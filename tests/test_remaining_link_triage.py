from __future__ import annotations

from obslayer.remaining_link_triage import build_remaining_link_triage_packet, classify_remaining_link


def test_remaining_triage_auto_keeps_generated_report_broken_link() -> None:
    item = classify_remaining_link(
        {
            "source": "Hermes/Reports/graphify-spark-corpus-c10-2026-06-27/GRAPH_REPORT.md",
            "raw": '#Community 0 - "Community 0"|Community 0',
            "target": '#Community 0 - "Community 0"',
            "status": "broken",
            "candidates": [],
        }
    )
    assert item["classification"] == "generated_report_auto_keep"
    assert item["operator_bucket"] == "accepted_no_apply"
    assert item["apply_authority"] == "none"


def test_remaining_triage_marks_soul_links_protected_manual() -> None:
    item = classify_remaining_link(
        {
            "source": "Hermes/Runtime Error Full Audit.md",
            "raw": "Hermes/Soul/Tool Policy Boundaries",
            "target": "Hermes/Soul/Tool Policy Boundaries",
            "status": "broken",
            "candidates": [],
        }
    )
    assert item["classification"] == "protected_cross_vault_manual"
    assert item["operator_bucket"] == "manual_protected"
    assert item["risk"] == "high"


def test_remaining_triage_marks_soul_vault_sources_protected_manual() -> None:
    item = classify_remaining_link(
        {
            "source": "Soul-Vault/Hermes/Soul Organism Kanban.md",
            "raw": "../../Memory-Vault/Hermes/Projects/foo|Foo",
            "target": "../../Memory-Vault/Hermes/Projects/foo",
            "status": "broken",
            "candidates": [],
        }
    )
    assert item["classification"] == "protected_cross_vault_manual"
    assert item["risk"] == "high"
    assert item["apply_authority"] == "none"


def test_remaining_triage_prefers_exact_graphify_candidate_without_apply() -> None:
    item = classify_remaining_link(
        {
            "source": "Hermes/HERMES_HOME.md",
            "raw": "Hermes/Reports/graphify-spark-corpus-c10-2026-06-27/README|Latest full corpus Graphify report",
            "target": "Hermes/Reports/graphify-spark-corpus-c10-2026-06-27/README",
            "status": "ambiguous",
            "candidates": [
                "Hermes/Reports/graphify-spark-corpus-c10-2026-06-27/README.md",
                "Hermes/Reports/graphify-spark-full-sandbox-2026-06-27/README.md",
            ],
        }
    )
    assert item["classification"] == "graphify_exact_path_preferred_no_apply"
    assert item["preferred_candidate"] == "Hermes/Reports/graphify-spark-corpus-c10-2026-06-27/README.md"
    assert item["live_mutation_authorized"] is False


def test_remaining_triage_packet_counts_only_broken_and_ambiguous() -> None:
    packet = build_remaining_link_triage_packet(
        wikilinks=[
            {"source": "A.md", "raw": "Known", "target": "Known", "status": "ok", "candidates": ["Known.md"]},
            {"source": "A.md", "raw": "Missing", "target": "Missing", "status": "broken", "candidates": []},
        ]
    )
    assert packet["summary"]["items"] == 1
    assert packet["summary"]["by_classification"] == {"real_broken_needs_target_discovery": 1}
    assert packet["summary"]["by_operator_bucket"] == {"target_discovery": 1}
    assert packet["summary"]["target_discovery_items"] == 1
    assert packet["summary"]["actionable_apply_items"] == 0
