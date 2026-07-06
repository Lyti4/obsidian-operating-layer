from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from obslayer.acceptance_bundle_doctor import (
    MODE,
    acceptance_bundle_doctor_to_markdown,
    doctor_acceptance_bundle,
    load_and_doctor_acceptance_bundle,
    write_acceptance_bundle_doctor_report,
)


def _good_bundle(repo: Path) -> dict:
    report = repo / "out" / "reports" / "slice" / "REPORT.md"
    spec = repo / "docs" / "spec-kit" / "41-acceptance-bundle-doctor.md"
    acceptance = repo / "docs" / "acceptance" / "index.md"
    report.parent.mkdir(parents=True)
    spec.parent.mkdir(parents=True)
    acceptance.parent.mkdir(parents=True)
    report.write_text("# report\n", encoding="utf-8")
    spec.write_text("# spec\n", encoding="utf-8")
    acceptance.write_text("# acceptance\n", encoding="utf-8")
    return {
        "mode": MODE,
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "apply_authority": "none",
        "target_paths": [],
        "findings": [],
        "artifacts": [
            {"name": "report", "path": "out/reports/slice/REPORT.md", "kind": "report", "required": True},
            {"name": "spec", "path": "docs/spec-kit/41-acceptance-bundle-doctor.md", "kind": "evidence", "required": True},
            {"name": "acceptance", "path": "docs/acceptance/index.md", "kind": "index", "required": True},
        ],
        "checks": [
            {"name": "unit", "command": "python -m pytest tests/test_acceptance_bundle_doctor.py -q", "status": "passed", "required": True},
            {"name": "diff", "command": "git diff --check", "status": "ok", "required": True},
        ],
    }


def test_acceptance_bundle_doctor_accepts_repo_only_bundle(tmp_path: Path) -> None:
    bundle = _good_bundle(tmp_path)

    report = doctor_acceptance_bundle(bundle, repo=tmp_path).to_dict()

    assert report["status"] == "accepted"
    assert report["findings"] == []
    assert report["safety"]["live_mutation_authorized"] is False
    assert report["safety"]["approval_manifest_created"] is False
    assert report["safety"]["apply_authority"] == "none"
    assert report["safety"]["targets"] == []


def test_acceptance_bundle_doctor_blocks_apply_authority(tmp_path: Path) -> None:
    bundle = _good_bundle(tmp_path)
    bundle["apply_authority"] = "apply"

    report = doctor_acceptance_bundle(bundle, repo=tmp_path)

    assert report.status == "blocked"
    assert any("apply_authority" in finding for finding in report.findings)


def test_acceptance_bundle_doctor_blocks_live_targets(tmp_path: Path) -> None:
    bundle = _good_bundle(tmp_path)
    bundle["target_paths"] = ["Notes/live.md"]

    report = doctor_acceptance_bundle(bundle, repo=tmp_path)

    assert report.status == "blocked"
    assert any("target paths" in finding for finding in report.findings)


def test_acceptance_bundle_doctor_blocks_artifact_outside_repo_allowed_roots(tmp_path: Path) -> None:
    outside = tmp_path.parent / "live-vault" / "note.md"
    outside.parent.mkdir(exist_ok=True)
    outside.write_text("secret-ish body should not be referenced\n", encoding="utf-8")
    bundle = _good_bundle(tmp_path)
    bundle["artifacts"].append({"name": "bad", "path": str(outside), "required": True})

    report = doctor_acceptance_bundle(bundle, repo=tmp_path)

    assert report.status == "blocked"
    assert any("must stay under repo" in finding for finding in report.findings)


def test_acceptance_bundle_doctor_blocks_failed_required_check(tmp_path: Path) -> None:
    bundle = _good_bundle(tmp_path)
    bundle["checks"][0]["status"] = "failed"

    report = doctor_acceptance_bundle(bundle, repo=tmp_path)

    assert report.status == "blocked"
    assert any("required check" in finding for finding in report.findings)
    assert any("reports failure" in finding for finding in report.findings)


def test_acceptance_bundle_doctor_loads_and_writes_report(tmp_path: Path) -> None:
    bundle = _good_bundle(tmp_path)
    bundle_path = tmp_path / "out" / "bundle.json"
    bundle_path.parent.mkdir(exist_ok=True)
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")

    report = load_and_doctor_acceptance_bundle(bundle_path, repo=tmp_path)
    json_path, md_path = write_acceptance_bundle_doctor_report(report, tmp_path / "out" / "doctor")
    markdown = acceptance_bundle_doctor_to_markdown(report)

    assert report.status == "accepted"
    assert json_path.is_file()
    assert md_path.is_file()
    assert "Acceptance Bundle Doctor" in markdown


def test_acceptance_bundle_doctor_cli_returns_zero_for_accepted(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    bundle = _good_bundle(tmp_path)
    bundle_path = tmp_path / "out" / "bundle.json"
    out_dir = tmp_path / "out" / "doctor"
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_acceptance_bundle_doctor.py"),
            "--repo",
            str(tmp_path),
            "--bundle",
            str(bundle_path),
            "--out-dir",
            str(out_dir),
            "--json-only",
        ],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    result = json.loads(completed.stdout)
    assert result["status"] == "accepted"
    assert (out_dir / "acceptance-bundle-doctor.json").is_file()
    assert (out_dir / "REPORT.md").is_file()


def test_acceptance_bundle_doctor_cli_returns_one_for_blocked(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    bundle = _good_bundle(tmp_path)
    bundle["live_mutation_authorized"] = True
    bundle_path = tmp_path / "out" / "bundle.json"
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_acceptance_bundle_doctor.py"),
            "--repo",
            str(tmp_path),
            "--bundle",
            str(bundle_path),
            "--json-only",
        ],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1, completed.stderr + completed.stdout
    result = json.loads(completed.stdout)
    assert result["status"] == "blocked"
    assert result["safety"]["live_mutation_authorized"] is False
