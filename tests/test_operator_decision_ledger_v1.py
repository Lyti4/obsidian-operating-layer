from __future__ import annotations

import json
from pathlib import Path

from obslayer.operator_decision_ledger_v1 import (
    append_decision_record,
    build_operator_decision_ledger,
    normalize_decision_record,
    serialize_operator_decision_ledger,
    write_operator_decision_ledger,
)


def test_normalize_decision_record_is_evidence_only_and_json_serializable() -> None:
    record = normalize_decision_record(
        {
            "timestamp": "2026-07-05T00:00:00Z",
            "id": "keep-operator-choice",
            "type": "accept-proposal",
            "actor": "dmitry",
            "reason": "proposal has bounded target refs",
            "target_refs": ["Memory-Vault/A.md", "Memory-Vault/A.md"],
            "proposal_refs": [{"path": "out/proposals/p.json", "kind": "proposal"}],
            "approval_manifest_refs": [{"path": "out/manifests/approved.json", "supplied_as": "data-only"}],
            "evidence_refs": ["out/reports/r.md", {"path": "out/reports/e.json", "kind": "evidence"}],
            "safety_flags": ["operator_selected", "operator_selected"],
            "live_mutation_authorized": True,
            "approval_manifest_created": True,
            "targets": ["must-not-be-carried-as-apply-target"],
        }
    )

    assert record["created_at"] == "2026-07-05T00:00:00Z"
    assert record["decision_id"] == "keep-operator-choice"
    assert record["decision_type"] == "accept-proposal"
    assert record["behavior"] == "evidence-only"
    assert record["live_mutation_authorized"] is False
    assert record["approval_manifest_created"] is False
    assert record["targets"] == []
    assert record["target_refs"] == ["Memory-Vault/A.md"]
    assert record["approval_manifest_refs"] == [{"path": "out/manifests/approved.json", "supplied_as": "data-only"}]
    assert "no_live_apply" in record["safety_flags"]
    assert "operator_selected" in record["safety_flags"]
    json.dumps(record, sort_keys=True)


def test_append_decision_record_returns_deterministic_order_and_deduped_refs() -> None:
    existing = [
        {
            "created_at": "2026-07-05T02:00:00Z",
            "decision_id": "second",
            "decision_type": "defer",
            "actor": "operator",
            "reason": "later",
            "evidence_refs": ["b", "a", "a"],
        }
    ]

    records = append_decision_record(
        existing,
        created_at="2026-07-05T01:00:00Z",
        decision_id="first",
        decision_type="accept-proposal",
        actor="operator",
        reason="earlier",
        evidence_refs=[{"path": "z"}, {"path": "a"}, {"path": "z"}],
    )

    assert [record["decision_id"] for record in records] == ["first", "second"]
    assert records[0]["evidence_refs"] == [{"path": "a"}, {"path": "z"}]
    assert records[1]["evidence_refs"] == ["a", "b"]


def test_ledger_serialization_is_stable_and_carries_no_live_apply_semantics() -> None:
    ledger = build_operator_decision_ledger(
        [
            {
                "created_at": "2026-07-05T02:00:00Z",
                "decision_id": "b",
                "decision_type": "defer",
                "actor": "operator",
                "reason": "needs review",
            },
            {
                "created_at": "2026-07-05T01:00:00Z",
                "decision_id": "a",
                "decision_type": "accept-proposal",
                "actor": "operator",
                "reason": "safe proposal refs only",
                "proposal_refs": ["out/proposals/a.json"],
            },
        ],
        ledger_id="ledger-test",
        created_at="2026-07-05T03:00:00Z",
    )

    payload = ledger.to_dict()
    assert payload["mode"] == "operator-decision-ledger-v1"
    assert payload["behavior"] == "evidence-only"
    assert payload["live_mutation_authorized"] is False
    assert payload["approval_manifest_created"] is False
    assert payload["targets"] == []
    assert payload["records"][0]["decision_id"] == "a"
    assert payload["records"][1]["decision_id"] == "b"
    assert "no_live_apply_authorized" in payload["reason_codes"]

    rendered_once = serialize_operator_decision_ledger(ledger)
    rendered_twice = serialize_operator_decision_ledger(ledger)
    assert rendered_once == rendered_twice
    assert rendered_once.endswith("\n")
    assert json.loads(rendered_once)["ledger_id"] == "ledger-test"


def test_write_operator_decision_ledger_writes_sorted_json(tmp_path: Path) -> None:
    out_path = tmp_path / "ledger.json"

    result = write_operator_decision_ledger(
        [
            {
                "created_at": "2026-07-05T00:00:00Z",
                "decision_id": "operator-approved-ref-only",
                "decision_type": "record-approval-reference",
                "actor": "operator",
                "reason": "approval manifest was supplied as an inert reference",
                "approval_manifest_refs": ["out/approval-manifest.json"],
            }
        ],
        out_path=out_path,
        ledger_id="write-test",
        created_at="2026-07-05T00:01:00Z",
    )

    assert result == {"status": "ok", "ledger": str(out_path)}
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["ledger_id"] == "write-test"
    assert data["approval_manifest_created"] is False
    assert data["records"][0]["approval_manifest_created"] is False
    assert data["records"][0]["approval_manifest_refs"] == ["out/approval-manifest.json"]
