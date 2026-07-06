from __future__ import annotations

import json
from pathlib import Path

import pytest

from obslayer.guardrails import GuardrailError
from obslayer.unified_operator_review_index import (
    SAFETY,
    build_unified_operator_review_index,
    write_unified_operator_review_index,
)


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_text(path: Path, text: str = "report\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_ready_index_from_operator_packet_and_docs_pointers(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    operator_packet = _write_json(
        repo / "out" / "reports" / "operator-review-packet" / "grouped-next5-smoke" / "operator-review-packet.json",
        {
            "mode": "obslayer.operator-review-packet.v1",
            "status": "ready_for_human_review",
            "review_items": [{"source_id": "item-1"}, {"source_id": "item-2"}],
            "safety": {
                "live_mutation_authorized": False,
                "approval_manifest_created": False,
                "apply_authority": "none",
                "target_paths": [],
            },
        },
    )
    report = _write_text(repo / "out" / "reports" / "operator-review-packet" / "grouped-next5-smoke" / "REPORT.md")
    docs_index = _write_text(repo / "docs" / "acceptance" / "index.md")

    index = build_unified_operator_review_index(repo=repo, artifacts=[operator_packet, report, docs_index])
    payload = index.to_dict()

    assert index.status == "ready_for_operator_review"
    assert payload["mode"] == "obslayer.unified-operator-review-index.v1"
    assert payload["safety"] == SAFETY
    assert payload["safety"]["target_paths"] == []
    assert payload["summary"] == {
        "total_artifacts": 3,
        "present_artifacts": 3,
        "missing_artifacts": 0,
        "ready_for_human_review_count": 1,
        "blocked_count": 0,
        "proposal_only_count": 1,
    }
    assert payload["artifacts"][0]["path"] == "out/reports/operator-review-packet/grouped-next5-smoke/operator-review-packet.json"
    assert payload["artifacts"][0]["status"] == "ready_for_human_review"
    assert payload["artifacts"][0]["review_items"] == 2
    assert payload["artifacts"][0]["safety"]["apply_authority"] == "none"
    assert payload["artifacts"][1]["kind"] == "report"
    assert payload["artifacts"][2]["kind"] == "doc"
    assert payload["next_gates"]


def test_missing_artifacts_are_counted_but_not_blockers(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    present = _write_text(repo / "docs" / "spec-kit" / "36-current-evidence-index.md", "proposal-only evidence index\n")
    missing = repo / "out" / "reports" / "operator-review-packet" / "grouped-next5-smoke" / "operator-review-packet.json"

    index = build_unified_operator_review_index(repo=repo, artifacts=[present, missing])

    assert index.status == "ready_for_operator_review"
    assert index.summary["total_artifacts"] == 2
    assert index.summary["present_artifacts"] == 1
    assert index.summary["missing_artifacts"] == 1
    assert index.summary["blocked_count"] == 0
    assert index.artifacts[1].exists is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("live_mutation_authorized", True),
        ("approval_manifest_created", True),
        ("approval_manifest_authority", True),
        ("apply_authority", "approved"),
    ],
)
def test_blocks_json_artifact_that_claims_apply_or_approval_authority(tmp_path: Path, field: str, value: object) -> None:
    repo = tmp_path / "repo"
    path = _write_json(
        repo / "out" / "reports" / "unsafe.json",
        {
            "mode": "unsafe.fixture",
            "status": "ready_for_human_review",
            field: value,
        },
    )

    index = build_unified_operator_review_index(repo=repo, artifacts=[path])

    assert index.status == "blocked"
    assert index.summary["blocked_count"] == 1
    assert index.artifacts[0].status == "blocked"
    assert any(field in note for note in index.artifacts[0].notes)
    assert index.safety == SAFETY


def test_path_guard_rejects_outside_repo_and_non_out_docs_paths(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    src_path = repo / "src" / "unsafe.json"
    src_path.parent.mkdir(parents=True, exist_ok=True)
    src_path.write_text("{}", encoding="utf-8")

    with pytest.raises(GuardrailError):
        build_unified_operator_review_index(repo=repo, artifacts=[outside])

    with pytest.raises(GuardrailError):
        build_unified_operator_review_index(repo=repo, artifacts=[src_path])


def test_path_guard_rejects_symlink_escape(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    link = repo / "out" / "reports" / "escape.json"
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(outside)

    with pytest.raises(GuardrailError):
        build_unified_operator_review_index(repo=repo, artifacts=[link])


def test_writes_json_and_report(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    artifact = _write_text(repo / "docs" / "acceptance" / "index.md", "proposal-only\n")
    index = build_unified_operator_review_index(repo=repo, artifacts=[artifact])

    json_path, report_path = write_unified_operator_review_index(index, repo / "out" / "reports" / "unified")

    assert json_path.name == "unified-operator-review-index.json"
    assert report_path.name == "REPORT.md"
    assert json.loads(json_path.read_text(encoding="utf-8"))["mode"] == "obslayer.unified-operator-review-index.v1"
    assert "Unified Operator Review Index" in report_path.read_text(encoding="utf-8")

def test_default_artifacts_include_candidate_volume_packet() -> None:
    from obslayer.unified_operator_review_index import DEFAULT_ARTIFACTS

    assert (
        "out/reports/candidate-volume-operator-packet/"
        "full-vault-proposal-only-20260706T182612Z/candidate-volume-operator-packet.json"
        in DEFAULT_ARTIFACTS
    )
    assert (
        "out/reports/candidate-volume-operator-packet/"
        "full-vault-proposal-only-20260706T182612Z/REPORT.md"
        in DEFAULT_ARTIFACTS
    )

def test_default_artifacts_do_not_include_stale_missing_remaining_link_json() -> None:
    from obslayer.unified_operator_review_index import DEFAULT_ARTIFACTS

    assert (
        "out/reports/remaining-link-suppression-gate-20260706T1420Z/"
        "remaining-link-suppression-gate.json"
        not in DEFAULT_ARTIFACTS
    )
