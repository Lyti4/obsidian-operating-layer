from __future__ import annotations

from obslayer.proposal_routing_contract_v1 import (
    ROUTE_AUTO_PROPOSE,
    ROUTE_BLOCKED_REFUSE,
    ROUTE_NEEDS_HUMAN_REVIEW,
    ROUTE_SUGGEST,
    route_proposal_candidate,
)


def _candidate(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "proposed_target": "Memory-Vault/Target.md",
        "confidence": 0.95,
        "top_two_gap": 20,
        "reason_codes": ["active_target_available"],
    }
    base.update(overrides)
    return base


def test_threshold_met_routes_to_auto_propose_without_apply_authority() -> None:
    decision = route_proposal_candidate(_candidate()).to_dict()

    assert decision["route"] == ROUTE_AUTO_PROPOSE
    assert "routing_contract_auto_propose_threshold_met" in decision["reason_codes"]
    assert decision["targets"] == []
    assert decision["dry_run_only"] is True
    assert decision["live_mutation_authorized"] is False
    assert decision["approval_manifest_created"] is False
    assert decision["approval_manifest_authority"] is False


def test_threshold_miss_routes_to_suggest_only() -> None:
    decision = route_proposal_candidate(_candidate(confidence=0.94)).to_dict()

    assert decision["route"] == ROUTE_SUGGEST
    assert "routing_contract_suggest_only" in decision["reason_codes"]


def test_ledger_prior_is_weak_and_never_makes_suggest_authoritative() -> None:
    decision = route_proposal_candidate(
        _candidate(confidence=0.10, top_two_gap=0),
        operator_decision_records=[
            {"decision_id": "accepted-before", "decision_type": "accept-proposal"}
        ],
    ).to_dict()

    assert decision["route"] == ROUTE_SUGGEST
    assert decision["ledger_prior"] == {
        "authority": False,
        "behavior": "weak-prior-only",
        "decision_ids": ["accepted-before"],
        "record_count": 1,
    }
    assert "operator_decision_ledger_weak_prior" in decision["reason_codes"]
    assert "ledger_prior_not_authoritative" in decision["safety_flags"]


def test_risky_candidate_routes_to_human_review_even_when_thresholds_pass() -> None:
    decision = route_proposal_candidate(
        _candidate(reason_codes=["ambiguous_candidates"])
    ).to_dict()

    assert decision["route"] == ROUTE_NEEDS_HUMAN_REVIEW
    assert "routing_contract_human_review_required" in decision["reason_codes"]


def test_protected_or_hard_stop_candidate_routes_to_blocked_refuse() -> None:
    protected = route_proposal_candidate(
        _candidate(proposed_target="_Archive/Target.md")
    ).to_dict()
    hard_stop = route_proposal_candidate(
        _candidate(hard_stop=True, reason_codes=["unsafe_candidate_hard_stop"])
    ).to_dict()

    assert protected["route"] == ROUTE_BLOCKED_REFUSE
    assert "protected_or_archive_target" in protected["reason_codes"]
    assert "protected_target_refused" in protected["safety_flags"]
    assert hard_stop["route"] == ROUTE_BLOCKED_REFUSE
    assert "routing_contract_refused" in hard_stop["reason_codes"]


def test_attempted_live_apply_or_approval_authority_routes_to_blocked_refuse() -> None:
    for payload in [
        _candidate(live_mutation_authorized=True),
        _candidate(approval_manifest_created=True),
        _candidate(approval_manifest_authority=True),
        _candidate(candidates=[{"path": "Memory-Vault/Target.md", "confidence": 1.0, "approval_manifest_authority": True}]),
    ]:
        decision = route_proposal_candidate(payload).to_dict()

        assert decision["route"] == ROUTE_BLOCKED_REFUSE
        assert "attempted_live_apply_or_approval_authority" in decision["reason_codes"]
        assert "attempted_authority_refused" in decision["safety_flags"]
        assert decision["live_mutation_authorized"] is False
        assert decision["approval_manifest_created"] is False
        assert decision["approval_manifest_authority"] is False


def test_no_route_authorizes_live_apply_or_manifest_creation() -> None:
    routes = [
        route_proposal_candidate(_candidate()),
        route_proposal_candidate(_candidate(confidence=0.1)),
        route_proposal_candidate(_candidate(reason_codes=["operator_review_required"])),
        route_proposal_candidate(_candidate(reason_codes=["unsafe_candidate_hard_stop"])),
    ]

    for decision in routes:
        payload = decision.to_dict()
        assert payload["route"] in {
            ROUTE_SUGGEST,
            ROUTE_AUTO_PROPOSE,
            ROUTE_NEEDS_HUMAN_REVIEW,
            ROUTE_BLOCKED_REFUSE,
        }
        assert payload["live_mutation_authorized"] is False
        assert payload["approval_manifest_created"] is False
        assert payload["approval_manifest_authority"] is False
        assert "no_live_apply" in payload["safety_flags"]
        assert "no_approval_manifest_authority" in payload["safety_flags"]
