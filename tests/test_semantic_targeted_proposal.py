from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from obslayer import GuardrailError
from obslayer.semantic_targeted_proposal import build_targeted_semantic_proposal


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_decision_packet(tmp_path: Path, decision: str = "promote-to-targeted-proposal") -> Path:
    out = repo_root() / "out" / "proposals" / "semantic-candidate-decisions" / f"targeted-{tmp_path.name}"
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": "semantic-candidate-decision-packet",
        "live_mutation_authorized": False,
        "targets": [],
        "groups": [
            {
                "name": "link_hygiene_reports",
                "decision": decision,
                "candidate_count": 2,
                "paths": ["Memory-Vault/Hermes/Reports/Obsidian Link Hygiene Scan.md"],
                "queries": ["link hygiene"],
                "next_action": "Create a small target-diff proposal.",
            }
        ],
    }
    path = out / "decision-packet.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_targeted_semantic_proposal_is_proposal_only(tmp_path: Path) -> None:
    packet = write_decision_packet(tmp_path)

    proposal = build_targeted_semantic_proposal(decision_packet_json=packet, proposal_id="t-test")

    assert proposal.mode == "semantic-targeted-proposal"
    assert proposal.status == "ready-for-operator-review"
    assert proposal.group == "link_hygiene_reports"
    assert proposal.targets == []
    assert proposal.live_mutation_authorized is False
    assert proposal.approval_manifest_created is False
    assert proposal.candidate_paths


def test_targeted_semantic_proposal_rejects_non_promotable_group(tmp_path: Path) -> None:
    packet = write_decision_packet(tmp_path, decision="keep-as-context")

    with pytest.raises(GuardrailError, match="not promotable"):
        build_targeted_semantic_proposal(decision_packet_json=packet)


def test_targeted_semantic_proposal_cli_writes_outputs(tmp_path: Path) -> None:
    repo = repo_root()
    packet = write_decision_packet(tmp_path)
    out_dir = repo / "out" / "proposals" / "semantic-targeted-proposals" / f"cli-{tmp_path.name}"

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_semantic_targeted_proposal.py"),
            "--decision-packet-json",
            str(packet),
            "--out-dir",
            str(out_dir),
            "--proposal-id",
            "t-cli",
        ],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["status"] == "ok"
    assert payload["targets"] == "0"
    assert Path(payload["proposal"]).is_file()
    assert Path(payload["report"]).is_file()
