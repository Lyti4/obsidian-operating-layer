from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from obslayer import GuardrailError
from obslayer.semantic_candidate_decision_packet import build_candidate_decision_packet


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_semantic_proposal(tmp_path: Path) -> Path:
    out = repo_root() / "out" / "proposals" / "semantic-query-reports" / f"decision-packet-{tmp_path.name}"
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": "semantic-query-proposal-only-report",
        "proposal_id": "p-test",
        "live_mutation_authorized": False,
        "targets": [],
        "candidates": [
            {
                "path": "Memory-Vault/Hermes/Reports/Obsidian Link Hygiene Scan.md",
                "queries": ["Obsidian link hygiene cleanup reports and broken links"],
                "best_score": 0.9,
                "hit_count": 1,
                "chunks": [0],
            },
            {
                "path": "Soul-Organism-Graphify-Vault/Graphify Corpus Index.md",
                "queries": ["Graphify corpus index and cross repository pattern map"],
                "best_score": 0.8,
                "hit_count": 1,
                "chunks": [0],
            },
            {
                "path": "Memory-Vault/Hermes/Reports/Codex Workspace Registry Latest.md",
                "queries": ["Nanobot graphify worker headroom codex orchestration"],
                "best_score": 0.7,
                "hit_count": 1,
                "chunks": [0],
            },
        ],
    }
    path = out / "proposal.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_candidate_decision_packet_groups_without_targets(tmp_path: Path) -> None:
    proposal = write_semantic_proposal(tmp_path)

    packet = build_candidate_decision_packet(semantic_proposal_json=proposal, packet_id="d-test")

    assert packet.mode == "semantic-candidate-decision-packet"
    assert packet.status == "ready-for-operator-review"
    assert packet.targets == []
    assert packet.live_mutation_authorized is False
    decisions = {group.name: group.decision for group in packet.groups}
    assert decisions["link_hygiene_reports"] == "promote-to-targeted-proposal"
    assert decisions["graphify_context"] == "keep-as-context"
    assert decisions["nanobot_orchestration_context"] == "promote-to-spec-kit-followup"


def test_candidate_decision_packet_rejects_live_mutation(tmp_path: Path) -> None:
    proposal = write_semantic_proposal(tmp_path)
    data = json.loads(proposal.read_text(encoding="utf-8"))
    data["live_mutation_authorized"] = True
    proposal.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(GuardrailError, match="must not authorize live mutation"):
        build_candidate_decision_packet(semantic_proposal_json=proposal)


def test_candidate_decision_packet_rejects_targets(tmp_path: Path) -> None:
    proposal = write_semantic_proposal(tmp_path)
    data = json.loads(proposal.read_text(encoding="utf-8"))
    data["targets"] = [{"path": "x.md"}]
    proposal.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(GuardrailError, match="must not contain edit targets"):
        build_candidate_decision_packet(semantic_proposal_json=proposal)


def test_candidate_decision_packet_cli_writes_outputs(tmp_path: Path) -> None:
    repo = repo_root()
    proposal = write_semantic_proposal(tmp_path)
    out_dir = repo / "out" / "proposals" / "semantic-candidate-decisions" / f"cli-{tmp_path.name}"

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_semantic_candidate_decision_packet.py"),
            "--semantic-proposal-json",
            str(proposal),
            "--out-dir",
            str(out_dir),
            "--packet-id",
            "d-cli",
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
    assert Path(payload["decision_packet"]).is_file()
    assert Path(payload["report"]).is_file()
