from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from obslayer.indexing_manifest_doctor import (
    IndexingManifestPolicy,
    build_indexing_doctor_report,
    build_indexing_manifest,
    manifest_from_dict,
    validate_indexing_manifest,
)


def _valid_manifest(tmp_path: Path):
    artifact = tmp_path / "out" / "reports" / "run" / "GRAPH_REPORT.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("# Graph report\n", encoding="utf-8")
    return build_indexing_manifest(
        files_seen=["Notes/A.md", "_Backups/old.md", "out/generated.md"],
        indexed=["Notes/A.md"],
        skipped=["_Backups/old.md", "out/generated.md"],
        protected_skipped=["_Backups/old.md"],
        generated_skipped=["out/generated.md"],
        broken_links=[{"source": "Notes/A.md", "target": "Missing"}],
        orphans=["Notes/Orphan.md"],
        duplicates=[],
        artifacts={"graph_report": str(artifact)},
        policy=IndexingManifestPolicy(
            live_mutation_enabled=False,
            max_files_per_run=50,
            protected_paths=["_Backups"],
            generated_paths=["out"],
        ),
        created_at="2026-07-06T00:00:00Z",
    )


def test_valid_manifest_with_protected_and_generated_skips_passes(tmp_path: Path) -> None:
    manifest = _valid_manifest(tmp_path)
    report = build_indexing_doctor_report(manifest, required_artifacts=["graph_report"])

    assert validate_indexing_manifest(manifest) == []
    assert report.status == "ready-for-operator-review"
    assert report.findings == []
    assert report.summary["protected_skipped"] == 1
    assert report.summary["generated_skipped"] == 1


def test_mismatch_counts_fail_validation(tmp_path: Path) -> None:
    manifest = build_indexing_manifest(
        files_seen=["Notes/A.md"],
        indexed=[],
        skipped=[],
        artifacts={},
        policy=IndexingManifestPolicy(),
    )

    findings = validate_indexing_manifest(manifest)

    assert "files_seen must equal indexed plus skipped" in findings


def test_max_files_per_run_76_fails_doctor(tmp_path: Path) -> None:
    manifest = build_indexing_manifest(
        files_seen=["Notes/A.md"],
        indexed=["Notes/A.md"],
        skipped=[],
        artifacts={},
        policy=IndexingManifestPolicy(max_files_per_run=76),
    )

    report = build_indexing_doctor_report(manifest)

    assert report.status == "blocked"
    assert any("76 <= 75" in finding for finding in report.findings)


def test_missing_required_artifact_fails_doctor(tmp_path: Path) -> None:
    manifest = build_indexing_manifest(
        files_seen=["Notes/A.md"],
        indexed=["Notes/A.md"],
        skipped=[],
        artifacts={"graph_report": str(tmp_path / "missing.md")},
        policy=IndexingManifestPolicy(),
    )

    report = build_indexing_doctor_report(manifest, required_artifacts=["graph_report"])

    assert report.status == "blocked"
    assert any("missing: graph_report" in finding for finding in report.findings)


def test_live_mutation_enabled_fails_doctor(tmp_path: Path) -> None:
    manifest = build_indexing_manifest(
        files_seen=["Notes/A.md"],
        indexed=["Notes/A.md"],
        skipped=[],
        artifacts={},
        policy=IndexingManifestPolicy(live_mutation_enabled=True),
    )

    report = build_indexing_doctor_report(manifest)

    assert report.status == "blocked"
    assert "live mutation enabled" in report.findings


def test_indexing_doctor_cli_writes_report(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    manifest = _valid_manifest(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    out_path = tmp_path / "doctor.json"
    manifest_path.write_text(json.dumps(manifest.to_dict()), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_indexing_doctor.py"),
            str(manifest_path),
            "--require-artifact",
            "graph_report",
            "--out",
            str(out_path),
        ],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    assert json.loads(completed.stdout)["status"] == "ready-for-operator-review"
    assert manifest_from_dict(json.loads(manifest_path.read_text(encoding="utf-8"))).files_seen == [
        "Notes/A.md",
        "_Backups/old.md",
        "out/generated.md",
    ]
    assert out_path.is_file()
