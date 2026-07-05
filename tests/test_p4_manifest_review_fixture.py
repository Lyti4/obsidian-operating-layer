from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "p4_manifest_review"


def _render(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, str):
        for key, replacement in replacements.items():
            value = value.replace(key, replacement)
        return value
    if isinstance(value, list):
        return [_render(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: _render(item, replacements) for key, item in value.items()}
    return value


def _materialize_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    vault = tmp_path / "fake_vault"
    shutil.copytree(FIXTURE_ROOT / "fake_vault", vault)
    proposal_path = tmp_path / "proposal.json"
    manifest_path = tmp_path / "approval_manifest.json"
    replacements = {
        "{fixture_vault}": str(vault),
        "{fixture_proposal}": str(proposal_path),
    }
    proposal = _render(json.loads((FIXTURE_ROOT / "proposal.json").read_text(encoding="utf-8")), replacements)
    manifest = _render(json.loads((FIXTURE_ROOT / "approval_manifest.json").read_text(encoding="utf-8")), replacements)
    proposal_path.write_text(json.dumps(proposal, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return vault, proposal_path, manifest_path


def _run_apply(repo: Path, proposal_path: Path, manifest_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_apply.py"),
            "--proposal",
            str(proposal_path),
            "--approval-manifest",
            str(manifest_path),
            "--apply",
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def test_p4_manifest_review_fixture_declares_expected_targets() -> None:
    expected = json.loads((FIXTURE_ROOT / "expected_targets.json").read_text(encoding="utf-8"))
    proposal = json.loads((FIXTURE_ROOT / "proposal.json").read_text(encoding="utf-8"))

    proposal_targets = sorted(target["path"] for target in proposal["targets"])
    assert proposal_targets == sorted(expected["targets"])


def test_p4_manifest_review_fails_closed_on_proposal_path_drift(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    vault, proposal_path, manifest_path = _materialize_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["proposal"] = str(tmp_path / "renamed-proposal.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    completed = _run_apply(repo, proposal_path, manifest_path)

    assert completed.returncode != 0
    assert "proposal does not match" in completed.stderr + completed.stdout
    assert (vault / "Notes" / "alpha.md").read_text(encoding="utf-8") == "alpha fixture\n"


def test_p4_manifest_review_fails_closed_on_target_list_drift(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    vault, proposal_path, manifest_path = _materialize_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["targets"].append(str(vault / "Notes" / "beta.md"))
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    completed = _run_apply(repo, proposal_path, manifest_path)

    assert completed.returncode != 0
    assert "extra_approved" in completed.stderr + completed.stdout
    assert (vault / "Notes" / "alpha.md").read_text(encoding="utf-8") == "alpha fixture\n"
    assert (vault / "Notes" / "beta.md").read_text(encoding="utf-8") == "beta fixture\n"


def test_p4_manifest_review_fails_closed_on_vault_root_drift(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    vault, proposal_path, manifest_path = _materialize_fixture(tmp_path)
    other_vault = tmp_path / "other_vault"
    (other_vault / "Notes").mkdir(parents=True)
    (other_vault / "Notes" / "alpha.md").write_text("other alpha\n", encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["vault_root"] = str(other_vault)
    manifest["targets"] = [str(other_vault / "Notes" / "alpha.md")]
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    completed = _run_apply(repo, proposal_path, manifest_path)

    assert completed.returncode != 0
    assert "vault does not match" in completed.stderr + completed.stdout
    assert (vault / "Notes" / "alpha.md").read_text(encoding="utf-8") == "alpha fixture\n"
    assert (other_vault / "Notes" / "alpha.md").read_text(encoding="utf-8") == "other alpha\n"
