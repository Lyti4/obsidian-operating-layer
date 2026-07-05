from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from obslayer.candidate_scorer_v1 import score_candidate, write_candidate_scorer_packet


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_inputs(tmp_path: Path) -> tuple[Path, Path]:
    notes = [
        {"path": "Memory-Vault/A.md", "top": "Memory-Vault"},
        {"path": "Memory-Vault/B.md", "top": "Memory-Vault"},
        {"path": "_Archive/B.md", "top": "_Archive", "protected_or_archive_surface": True},
        {"path": "Soul/B.md", "top": "Soul", "soul_protected": True},
    ]
    wikilinks = [
        {
            "source": "Memory-Vault/A.md",
            "status": "ambiguous",
            "raw": "B",
            "candidates": ["Memory-Vault/B.md", "_Archive/B.md"],
        },
        {
            "source": "Memory-Vault/A.md",
            "status": "broken",
            "raw": "Soul/B",
            "candidates": ["Soul/B.md"],
        },
    ]
    notes_path = tmp_path / "notes-index.jsonl"
    notes_path.write_text("\n".join(json.dumps(note) for note in notes) + "\n", encoding="utf-8")
    wikilinks_path = tmp_path / "wikilinks.jsonl"
    wikilinks_path.write_text("\n".join(json.dumps(link) for link in wikilinks) + "\n", encoding="utf-8")
    return notes_path, wikilinks_path


def test_score_candidate_prefers_active_target_and_records_safety_fields() -> None:
    scored = score_candidate(
        link={
            "source": "Memory-Vault/A.md",
            "status": "ambiguous",
            "candidates": [
                "_Backups/old/Memory-Vault/B.md",
                "Memory-Vault/B.md",
            ],
        },
        notes_by_path={
            "Memory-Vault/A.md": {
                "path": "Memory-Vault/A.md",
                "top": "Memory-Vault",
                "protected_or_archive_surface": False,
            },
            "Memory-Vault/B.md": {
                "path": "Memory-Vault/B.md",
                "top": "Memory-Vault",
                "protected_or_archive_surface": False,
            },
            "_Backups/old/Memory-Vault/B.md": {
                "path": "_Backups/old/Memory-Vault/B.md",
                "top": "_Backups",
                "protected_or_archive_surface": True,
            },
        },
    )

    assert scored["behavior"] == "evidence-only"
    assert scored["live_mutation_authorized"] is False
    assert scored["approval_manifest_created"] is False
    assert scored["review_required"] is True
    assert scored["hard_stop"] is True
    assert scored["top_two_gap"] > 0
    assert "candidate_scorer_evidence_only" in scored["reason_codes"]
    assert "operator_review_required" in scored["reason_codes"]

    active = scored["candidates"][0]
    backup = scored["candidates"][1]
    assert active["path"] == "Memory-Vault/B.md"
    assert active["confidence"] > backup["confidence"]
    assert active["review_required"] is True
    assert active["hard_stop"] is False
    assert "active_target_available" in active["reason_codes"]
    assert active["safety_flags"] == ["ambiguous_link_requires_review"]
    assert active["feature_breakdown"]["candidate_archive_penalty"] == 0

    assert backup["hard_stop"] is True
    assert backup["review_required"] is True
    assert "protected_or_archive_target" in backup["reason_codes"]
    assert "backup_shadow_target" in backup["reason_codes"]
    assert "archive_or_shadow_target_hard_stop" in backup["safety_flags"]
    assert backup["feature_breakdown"]["candidate_archive_penalty"] < 0


def test_score_candidate_hard_stops_redirect_duplicate_and_missing_candidates() -> None:
    scored = score_candidate(
        link={
            "source": "Memory-Vault/A.md",
            "status": "ambiguous",
            "candidates": [
                "Redirects/B.md",
                "Duplicates/B copy.md",
                "Memory-Vault/Missing.md",
            ],
        },
        notes_by_path={
            "Memory-Vault/A.md": {
                "path": "Memory-Vault/A.md",
                "top": "Memory-Vault",
                "protected_or_archive_surface": False,
            },
            "Redirects/B.md": {
                "path": "Redirects/B.md",
                "top": "Redirects",
                "canonical_path": "Memory-Vault/B.md",
            },
            "Duplicates/B copy.md": {
                "path": "Duplicates/B copy.md",
                "top": "Duplicates",
                "duplicate_of": "Memory-Vault/B.md",
            },
        },
    )

    by_path = {item["path"]: item for item in scored["candidates"]}
    assert scored["review_required"] is True
    assert scored["hard_stop"] is True
    assert scored["top_two_gap"] >= 0

    assert "redirect_shadow_target" in by_path["Redirects/B.md"]["reason_codes"]
    assert by_path["Redirects/B.md"]["hard_stop"] is True
    assert "canonical_shadow_target" in by_path["Redirects/B.md"]["reason_codes"]

    assert "duplicate_shadow_target" in by_path["Duplicates/B copy.md"]["reason_codes"]
    assert by_path["Duplicates/B copy.md"]["hard_stop"] is True

    assert "candidate_missing_from_index" in by_path["Memory-Vault/Missing.md"]["reason_codes"]
    assert by_path["Memory-Vault/Missing.md"]["review_required"] is True
    assert by_path["Memory-Vault/Missing.md"]["hard_stop"] is True


def test_score_candidate_hard_stops_soul_or_protected_candidate() -> None:
    scored = score_candidate(
        link={
            "source": "Memory-Vault/A.md",
            "status": "ok",
            "candidates": ["Soul/B.md"],
        },
        notes_by_path={
            "Memory-Vault/A.md": {"path": "Memory-Vault/A.md", "top": "Memory-Vault"},
            "Soul/B.md": {"path": "Soul/B.md", "top": "Soul", "soul_protected": True},
        },
    )

    assert scored["live_mutation_authorized"] is False
    assert scored["approval_manifest_created"] is False
    assert scored["targets"] == []
    assert scored["apply_authority"] == "none"
    assert scored["review_required"] is True
    assert scored["hard_stop"] is True
    assert "soul_or_protected_surface" in scored["reason_codes"]
    assert scored["candidates"][0]["hard_stop"] is True
    assert "soul_or_protected_surface_hard_stop" in scored["candidates"][0]["safety_flags"]


def test_candidate_scorer_writer_outputs_json_and_report_without_authority(tmp_path: Path) -> None:
    notes_path, wikilinks_path = write_inputs(tmp_path)
    out_dir = tmp_path / "candidate-scorer-v1"

    result = write_candidate_scorer_packet(
        notes_index_jsonl=notes_path,
        wikilinks_jsonl=wikilinks_path,
        out_dir=out_dir,
        packet_id="candidate-test",
    )

    assert result == {
        "status": "ok",
        "candidate_scorer": str(out_dir / "candidate-scorer-v1.json"),
        "report": str(out_dir / "REPORT.md"),
    }
    payload = json.loads((out_dir / "candidate-scorer-v1.json").read_text(encoding="utf-8"))
    assert payload["mode"] == "repo-only/evidence-only"
    assert payload["behavior"] == "evidence-only"
    assert payload["live_mutation_authorized"] is False
    assert payload["approval_manifest_created"] is False
    assert payload["targets"] == []
    assert payload["apply_authority"] == "none"
    assert payload["summary"]["candidate_packets"] == 2
    assert payload["summary"]["hard_stop_packets"] == 2
    assert payload["candidate_packets"][0]["top_two_gap"] > 0
    for packet in payload["candidate_packets"]:
        assert packet["reason_codes"]
        assert "top_two_gap" in packet
        for candidate in packet["candidates"]:
            assert candidate["reason_codes"]
            assert candidate["feature_breakdown"]
    report = (out_dir / "REPORT.md").read_text(encoding="utf-8")
    assert "Candidate scorer v1" in report
    assert "grants no apply authority" in report


def test_candidate_scorer_cli_outputs_artifact_paths(tmp_path: Path) -> None:
    notes_path, wikilinks_path = write_inputs(tmp_path)
    out_dir = tmp_path / "cli-out"

    completed = subprocess.run(
        [
            sys.executable,
            str(repo_root() / "tools" / "obsidian_candidate_scorer.py"),
            "--notes-index-jsonl",
            str(notes_path),
            "--wikilinks-jsonl",
            str(wikilinks_path),
            "--out-dir",
            str(out_dir),
            "--packet-id",
            "candidate-cli-test",
        ],
        cwd=repo_root(),
        check=True,
        text=True,
        capture_output=True,
    )

    result = json.loads(completed.stdout)
    assert result["status"] == "ok"
    assert result["candidate_scorer"] == str(out_dir / "candidate-scorer-v1.json")
    payload = json.loads((out_dir / "candidate-scorer-v1.json").read_text(encoding="utf-8"))
    assert payload["packet_id"] == "candidate-cli-test"
    assert payload["live_mutation_authorized"] is False
    assert payload["approval_manifest_created"] is False
