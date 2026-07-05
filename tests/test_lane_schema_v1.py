from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from obslayer.lane_schema_v1 import build_lane_schema_packet, score_candidate


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    lanes = {
        "status": "ok",
        "mode": "actionable_full_vault_analysis_lanes",
        "source_run": str(tmp_path),
        "live_mutation_authorized": False,
        "next_lanes": [
            {
                "id": "active-memory-broken-links",
                "label": "Active memory broken links",
                "approval_class": "proposal_only",
                "reason_codes": ["active_memory_broken_link", "operator_review_required"],
                "forbidden_actions": ["live_vault_mutation", "approval_manifest_creation"],
            }
        ],
    }
    lanes_path = tmp_path / "actionable-lanes.json"
    lanes_path.write_text(json.dumps(lanes), encoding="utf-8")

    notes = [
        {
            "path": "Memory-Vault/A.md",
            "top": "Memory-Vault",
            "protected_or_archive_surface": False,
            "wikilink_count": 2,
            "heading_count": 1,
            "bytes": 100,
            "sha256": "aaa",
        },
        {
            "path": "_Backups/old/Memory-Vault/A.md",
            "top": "_Backups",
            "protected_or_archive_surface": True,
            "wikilink_count": 2,
            "heading_count": 1,
            "bytes": 100,
            "sha256": "aaa",
        },
        {
            "path": "Memory-Vault/B.md",
            "top": "Memory-Vault",
            "protected_or_archive_surface": False,
            "wikilink_count": 0,
            "heading_count": 1,
            "bytes": 200,
            "sha256": "bbb",
        },
    ]
    notes_path = tmp_path / "notes-index.jsonl"
    notes_path.write_text("\n".join(json.dumps(item) for item in notes) + "\n", encoding="utf-8")

    wikilinks = [
        {
            "source": "Memory-Vault/A.md",
            "raw": "B",
            "target": "B",
            "status": "ambiguous",
            "candidates": ["Memory-Vault/B.md", "_Backups/old/Memory-Vault/B.md"],
        },
        {
            "source": "_Backups/old/Memory-Vault/A.md",
            "raw": "B",
            "target": "B",
            "status": "broken",
            "candidates": [],
        },
    ]
    wikilinks_path = tmp_path / "wikilinks.jsonl"
    wikilinks_path.write_text("\n".join(json.dumps(item) for item in wikilinks) + "\n", encoding="utf-8")
    return lanes_path, notes_path, wikilinks_path


def test_lane_schema_packet_is_safe_and_evidence_only(tmp_path: Path) -> None:
    lanes_path, notes_path, wikilinks_path = write_inputs(tmp_path)

    packet = build_lane_schema_packet(
        actionable_lanes_json=lanes_path,
        notes_index_jsonl=notes_path,
        wikilinks_jsonl=wikilinks_path,
        packet_id="lane-test",
        created_at="2026-07-05T00:00:00Z",
    )
    data = packet.to_dict()

    assert data["mode"] == "lane-schema-v1"
    assert data["live_mutation_authorized"] is False
    assert data["approval_manifest_created"] is False
    assert data["targets"] == []
    assert data["approval_classes"] == ["proposal_only", "shadow_index_evidence_only"]
    assert "live_vault_mutation" in data["forbidden_actions"]
    assert "approval_manifest_creation" in data["forbidden_actions"]
    assert "active_memory_broken_link" in data["reason_codes"]
    assert "archive_shadow_evidence_only" in data["reason_codes"]
    assert data["archive_shadow_index"]["behavior"] == "evidence-only"
    assert data["archive_shadow_index"]["live_mutation_authorized"] is False
    assert data["archive_shadow_index"]["approval_manifest_created"] is False
    assert data["archive_shadow_index"]["entries"][0]["active_path"] == "Memory-Vault/A.md"
    assert data["candidate_scorer"]["candidates"][0]["feature_breakdown"]["status"] == "ambiguous"
    assert data["candidate_scorer"]["top_two_gap"] >= 0


def test_score_candidate_reports_feature_breakdown_and_top_two_gap() -> None:
    scored = score_candidate(
        link={
            "source": "Memory-Vault/A.md",
            "status": "ambiguous",
            "candidates": ["Memory-Vault/B.md", "_Backups/old/Memory-Vault/B.md"],
        },
        notes_by_path={
            "Memory-Vault/A.md": {"protected_or_archive_surface": False},
            "Memory-Vault/B.md": {"protected_or_archive_surface": False},
            "_Backups/old/Memory-Vault/B.md": {"protected_or_archive_surface": True},
        },
    )

    assert scored["top_two_gap"] > 0
    assert scored["candidates"][0]["path"] == "Memory-Vault/B.md"
    assert scored["candidates"][0]["feature_breakdown"]["candidate_archive_penalty"] == 0
    assert scored["candidates"][1]["feature_breakdown"]["candidate_archive_penalty"] < 0


def test_lane_schema_cli_writes_machine_readable_packets(tmp_path: Path) -> None:
    lanes_path, notes_path, wikilinks_path = write_inputs(tmp_path)
    repo = repo_root()
    out_dir = repo / "out" / "reports" / "lane-schema-v1" / f"cli-{tmp_path.name}"

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_lane_schema_v1.py"),
            "--actionable-lanes-json",
            str(lanes_path),
            "--notes-index-jsonl",
            str(notes_path),
            "--wikilinks-jsonl",
            str(wikilinks_path),
            "--out-dir",
            str(out_dir),
            "--packet-id",
            "lane-cli",
        ],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    result = json.loads(completed.stdout)
    assert result["status"] == "ok"
    assert Path(result["packet"]).is_file()
    assert Path(result["report"]).is_file()
    payload = json.loads(Path(result["packet"]).read_text(encoding="utf-8"))
    assert payload["mode"] == "lane-schema-v1"
    assert payload["live_mutation_authorized"] is False
    assert payload["approval_manifest_created"] is False


def test_lane_schema_packet_keeps_candidate_scorer_evidence_only_without_candidates(
    tmp_path: Path,
) -> None:
    lanes_path = tmp_path / "actionable-lanes.json"
    lanes_path.write_text(
        json.dumps(
            {
                "status": "ok",
                "mode": "actionable_full_vault_analysis_lanes",
                "next_lanes": [],
            }
        ),
        encoding="utf-8",
    )
    notes_path = tmp_path / "notes-index.jsonl"
    notes_path.write_text(
        json.dumps(
            {
                "path": "Memory-Vault/A.md",
                "top": "Memory-Vault",
                "protected_or_archive_surface": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    wikilinks_path = tmp_path / "wikilinks.jsonl"
    wikilinks_path.write_text(
        json.dumps(
            {
                "source": "Memory-Vault/A.md",
                "raw": "Missing",
                "target": "Missing",
                "status": "broken",
                "candidates": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    packet = build_lane_schema_packet(
        actionable_lanes_json=lanes_path,
        notes_index_jsonl=notes_path,
        wikilinks_jsonl=wikilinks_path,
        packet_id="lane-empty-scorer",
        created_at="2026-07-05T00:00:00Z",
    )

    scorer = packet.to_dict()["candidate_scorer"]
    assert scorer["behavior"] == "evidence-only"
    assert scorer["live_mutation_authorized"] is False
    assert scorer["approval_manifest_created"] is False
    assert scorer["candidates"] == []
    assert scorer["top_two_gap"] == 0
    assert "candidate_scorer_evidence_only" in scorer["reason_codes"]
