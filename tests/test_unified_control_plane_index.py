from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from obslayer.guardrails import GuardrailError
from obslayer.unified_control_plane_index import (
    MODE,
    SAFETY,
    build_unified_control_plane_index,
    write_unified_control_plane_index,
)


def _write_text(path: Path, text: str = "report\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _canonical_docs(repo: Path) -> None:
    _write_text(
        repo / "docs" / "acceptance" / "index.md",
        "Unified operator review index v1 accepted\n"
        "R7 narrow approved apply pilot accepted for historical live apply only\n",
    )
    for name in (
        "35-agentic-os-control-plane-map.md",
        "36-current-evidence-index.md",
        "38-unified-queue-state-decision-surface-v1.md",
        "40-indexing-manifest-and-doctor-contract.md",
        "47-unified-operator-review-index.md",
        "49-manifest-candidate-selector.md",
        "50-unified-control-plane-evidence-index.md",
    ):
        _write_text(repo / "docs" / "spec-kit" / name, f"# {name}\nStatus: accepted\n")
    _write_text(repo / "docs" / "triage" / "kanban-board.md", "status: active\n")


def test_builds_contract_with_stable_keys_and_ready_artifact(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _canonical_docs(repo)
    report = _write_text(
        repo / "out" / "reports" / "manifest-candidate-selector" / "20260707T010203Z" / "REPORT.md",
        "Concrete proposal candidates: 3\n"
        "next actions: Hermes operator review\n"
        "live_mutation_authorized: false\n"
        "approval_manifest_created: false\n"
        "apply_authority: none\n",
    )

    index = build_unified_control_plane_index(repo=repo, artifacts=[report])
    payload = index.to_dict()

    assert payload["mode"] == MODE
    assert payload["safety"] == SAFETY
    assert payload["queue_state"]["ready_for_operator_review"] == 1
    assert payload["queue_state"]["blocked"] == 0
    assert payload["blockers"] == []
    assert len(payload["canonical_docs"]) == 9
    assert any(doc["path"] == "docs/spec-kit/50-unified-control-plane-evidence-index.md" for doc in payload["canonical_docs"])
    artifact = payload["evidence_artifacts"][0]
    assert artifact["path"] == "out/reports/manifest-candidate-selector/20260707T010203Z/REPORT.md"
    assert artifact["stable_key"] == "obslayer.report.manifest-candidate-selector.20260707T010203Z"
    assert artifact["artifact_family"] == "manifest-candidate-selector"
    assert artifact["artifact_stamp"] == "20260707T010203Z"
    assert artifact["source_path"] == artifact["path"]
    assert artifact["canonical_doc"] == "docs/spec-kit/49-manifest-candidate-selector.md"
    assert artifact["classification"] == "ready_for_operator_review"
    assert artifact["authority_state"] == "proposal_only"
    assert artifact["safe_to_dispatch"] is True
    assert payload["worker_signals"][0]["recommended_owner"] == "Hermes"
    assert payload["next_actions"]


def test_missing_optional_paths_are_warnings_not_crashes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _canonical_docs(repo)
    missing = repo / "out" / "reports" / "nanobot-cron-scout" / "20260707T093200Z" / "REPORT.md"

    index = build_unified_control_plane_index(repo=repo, artifacts=[missing])
    artifact = index.to_dict()["evidence_artifacts"][0]

    assert artifact["exists"] is False
    assert artifact["classification"] == "missing_optional"
    assert artifact["authority_state"] == "none"
    assert index.queue_state["blocked"] == 0
    assert any("missing optional artifact" in warning for warning in index.warnings)


def test_missing_required_canonical_docs_are_blockers(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write_text(repo / "docs" / "acceptance" / "index.md", "accepted\n")

    index = build_unified_control_plane_index(repo=repo, artifacts=[])

    assert index.queue_state["blocked"] == 7
    assert len(index.blockers) == 7
    assert all(blocker.startswith("missing required canonical doc: docs/spec-kit/") for blocker in index.blockers)


@pytest.mark.parametrize(
    "text",
    [
        "provider quota exceeded while reviewing\n",
        "OAuth auth missing for Nanobot\n",
        "dry-run no-op empty result\n",
        "runtime failure without project evidence\n",
    ],
)
def test_noise_reports_are_classified_as_noise_or_trash(tmp_path: Path, text: str) -> None:
    repo = tmp_path / "repo"
    _canonical_docs(repo)
    report = _write_text(repo / "out" / "reports" / "nanobot-cron-scout" / "20260707T010203Z" / "REPORT.md", text)

    index = build_unified_control_plane_index(repo=repo, artifacts=[report])

    assert index.evidence_artifacts[0].classification == "noise_or_trash"
    assert index.evidence_artifacts[0].authority_state == "none"
    assert index.queue_state["noise_or_trash"] == 1
    assert index.queue_state["blocked"] == 0


def test_historical_accepted_live_apply_is_not_active_blocker(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _canonical_docs(repo)
    report = _write_text(
        repo / "out" / "proposals" / "working-note-link-archive-duplicate-live-apply" / "20260705T083603Z" / "REPORT.md",
        "Live apply completed after explicit operator approval.\n"
        "approval manifest used, backup recorded, post-verify passed.\n",
    )

    index = build_unified_control_plane_index(repo=repo, artifacts=[report])
    artifact = index.evidence_artifacts[0]

    assert artifact.classification == "accepted_or_closed_evidence"
    assert artifact.authority_state == "historical_accepted"
    assert index.queue_state["blocked"] == 0


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("live_mutation_authorized", True),
        ("approval_manifest_created", True),
        ("approval_manifest_authority", True),
        ("apply_authority", "approved"),
        ("target_paths", ["Memory-Vault/file.md"]),
    ],
)
def test_active_safety_violations_are_blocked(tmp_path: Path, field: str, value: object) -> None:
    repo = tmp_path / "repo"
    _canonical_docs(repo)
    report = _write_json(
        repo / "out" / "reports" / "unsafe" / "20260707T010203Z" / "unsafe.json",
        {
            "mode": "fixture",
            "status": "ready_for_operator_review",
            "safety": {
                "live_mutation_authorized": False,
                "approval_manifest_created": False,
                "approval_manifest_authority": False,
                "apply_authority": "none",
                "target_paths": [],
                field: value,
            },
        },
    )

    index = build_unified_control_plane_index(repo=repo, artifacts=[report])
    artifact = index.evidence_artifacts[0]

    assert artifact.classification == "blocked"
    assert artifact.authority_state == "requires_explicit_approval"
    assert index.queue_state["blocked"] == 1
    assert index.blockers


def test_write_requires_unified_control_plane_report_root(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _canonical_docs(repo)
    index = build_unified_control_plane_index(repo=repo, artifacts=[])

    with pytest.raises(GuardrailError):
        write_unified_control_plane_index(index, repo / "out" / "reports" / "other")

    json_path, report_path = write_unified_control_plane_index(
        index,
        repo / "out" / "reports" / "unified-control-plane-index" / "smoke",
    )

    assert json_path.name == "control-plane-index.json"
    assert report_path.name == "REPORT.md"
    assert json.loads(json_path.read_text(encoding="utf-8"))["mode"] == MODE
    assert "Unified Control-Plane Evidence Index" in report_path.read_text(encoding="utf-8")


def test_path_guard_rejects_escape_and_unapproved_inputs(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _canonical_docs(repo)
    outside = _write_text(tmp_path / "REPORT.md")
    src = _write_text(repo / "src" / "REPORT.md")

    with pytest.raises(GuardrailError):
        build_unified_control_plane_index(repo=repo, artifacts=[outside])

    with pytest.raises(GuardrailError):
        build_unified_control_plane_index(repo=repo, artifacts=[src])


def test_cli_writes_expected_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _canonical_docs(repo)
    _write_text(
        repo / "out" / "reports" / "manifest-candidate-selector" / "20260707T010203Z" / "REPORT.md",
        "concrete review item\napply_authority: none\n",
    )
    out_dir = repo / "out" / "reports" / "unified-control-plane-index" / "smoke"

    result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve().parents[1] / "tools" / "obsidian_unified_control_plane_index.py"),
            "--repo",
            str(repo),
            "--out-dir",
            str(out_dir),
            "--artifact",
            "out/reports/manifest-candidate-selector/20260707T010203Z/REPORT.md",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert (out_dir / "control-plane-index.json").is_file()
    assert (out_dir / "REPORT.md").is_file()


def test_default_discovery_uses_latest_per_known_family(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _canonical_docs(repo)
    _write_text(
        repo / "out" / "reports" / "manifest-candidate-selector" / "20260101T000000Z" / "REPORT.md",
        "old next action\n",
    )
    latest = _write_text(
        repo / "out" / "reports" / "manifest-candidate-selector" / "20260707T010203Z" / "REPORT.md",
        "new concrete proposal candidates\n",
    )

    index = build_unified_control_plane_index(repo=repo)
    paths = {artifact.path for artifact in index.evidence_artifacts}

    assert latest.relative_to(repo).as_posix() in paths
    assert "out/reports/manifest-candidate-selector/20260101T000000Z/REPORT.md" not in paths


def test_include_out_glob_is_operator_selected_and_bounded(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _canonical_docs(repo)
    selected = _write_text(
        repo / "out" / "proposals" / "manual-family" / "20260707T010203Z" / "REPORT.md",
        "next action\n",
    )

    index = build_unified_control_plane_index(
        repo=repo,
        artifacts=[],
        include_out_globs=["out/proposals/manual-family/*/REPORT.md"],
    )

    assert [artifact.path for artifact in index.evidence_artifacts] == [selected.relative_to(repo).as_posix()]

    with pytest.raises(GuardrailError):
        build_unified_control_plane_index(repo=repo, artifacts=[], include_out_globs=["../*.json"])


def test_stale_markdown_report_is_not_dispatch_ready(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _canonical_docs(repo)
    stale = _write_text(
        repo / "out" / "reports" / "manifest-candidate-selector" / "grouped-next5-smoke" / "REPORT.md",
        "operator review next action but historical/stale and must not be reused; noop_already_applied\n",
    )

    index = build_unified_control_plane_index(repo=repo, artifacts=[stale])
    artifact = index.evidence_artifacts[0]

    assert artifact.classification == "stale"
    assert artifact.safe_to_dispatch is False


def test_no_candidate_review_packet_is_informational_checkpoint(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _canonical_docs(repo)
    packet = _write_text(
        repo / "out" / "reports" / "operator-review-packet" / "hermes-acceptance" / "packet.json",
        json.dumps({"status": "no_candidate", "review_items": [], "next_action": "do not request live approval"}),
    )

    index = build_unified_control_plane_index(repo=repo, artifacts=[packet])
    artifact = index.evidence_artifacts[0]

    assert artifact.classification == "stale"
    assert artifact.safe_to_dispatch is False


def test_empty_candidate_volume_checkpoint_is_not_dispatch_ready(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _canonical_docs(repo)
    checkpoint = _write_text(
        repo / "out" / "reports" / "candidate-volume-operator-packet" / "full-vault-proposal-only-20260706T182612Z" / "packet.json",
        json.dumps({"proposal": {"targets_count": 0, "first_manifest_candidate_queue": []}, "next_action": "operator review"}),
    )

    index = build_unified_control_plane_index(repo=repo, artifacts=[checkpoint])
    artifact = index.evidence_artifacts[0]

    assert artifact.classification == "stale"
    assert artifact.safe_to_dispatch is False
