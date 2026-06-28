from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import validate

from obslayer import (
    GuardrailError,
    build_indexing_spike_evaluation,
    classify_index_tool,
    hash_vault_tree,
    load_indexing_candidate_record,
    normalize_index_tool,
)
from obslayer.indexing_spike import safe_indexing_report_dir


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def candidate_record() -> Path:
    return repo_root() / "docs" / "spec-kit" / "research" / "sample-adapter-records" / "dalecb-obsidian-semantic-mcp.json"


def adapter_schema() -> Path:
    return repo_root() / "docs" / "spec-kit" / "schemas" / "adapter-metadata.schema.json"


def make_sandbox(tmp_path: Path) -> Path:
    sandbox = repo_root() / "out" / "sandbox-vaults" / f"pytest-{tmp_path.name}"
    if sandbox.exists():
        shutil.rmtree(sandbox)
    (sandbox / "Notes").mkdir(parents=True)
    (sandbox / "Notes" / "alpha.md").write_text(
        "---\ntags: [safety, obsidian]\n---\n# Alpha\nhello [[Beta]]\n",
        encoding="utf-8",
    )
    (sandbox / "Notes" / "Beta.md").write_text("# Beta\nbackup apply verify\n", encoding="utf-8")
    return sandbox


def test_sample_candidate_record_matches_adapter_schema() -> None:
    validate(
        instance=json.loads(candidate_record().read_text(encoding="utf-8")),
        schema=json.loads(adapter_schema().read_text(encoding="utf-8")),
    )


def test_load_indexing_candidate_record_accepts_dalecb_contract() -> None:
    record = load_indexing_candidate_record(candidate_record())

    assert record["kind"] == "knowledge-indexer"
    assert record["direct_write_enabled"] is False
    assert record["sandbox_required"] is True
    assert record["exposed_tools"] == ["search_notes", "read_note", "index_vault", "index_status"]
    assert record["embedding_policy"]["local_only"] is True


def test_load_indexing_candidate_record_rejects_write_tool(tmp_path: Path) -> None:
    bad = json.loads(candidate_record().read_text(encoding="utf-8"))
    bad["exposed_tools"].append("delete_note")
    bad_path = tmp_path / "bad-indexer.json"
    bad_path.write_text(json.dumps(bad), encoding="utf-8")

    with pytest.raises(GuardrailError):
        load_indexing_candidate_record(bad_path)


def test_index_tool_classifier_allows_derived_index_tools_and_refuses_mutations() -> None:
    assert classify_index_tool("search_notes") == "allow-readonly-index"
    assert classify_index_tool("read_note") == "allow-readonly-index"
    assert classify_index_tool("index_vault") == "allow-readonly-index"
    assert classify_index_tool("index_status") == "allow-readonly-index"

    refused = normalize_index_tool("write_note")
    assert refused["status"] == "refused"
    assert refused["proposal_required"] is True
    assert refused["executed"] is False


def test_build_indexing_spike_evaluation_is_no_write_and_hash_bound(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    sandbox = make_sandbox(tmp_path)
    before = hash_vault_tree(sandbox)

    evaluation = build_indexing_spike_evaluation(candidate_record=candidate_record(), sandbox_vault=sandbox)
    after = hash_vault_tree(sandbox)

    assert before["tree_sha256"] == after["tree_sha256"]
    assert evaluation.candidate == "DalecB/obsidian-semantic-mcp"
    assert evaluation.verification["external_candidate_executed"] is False
    assert evaluation.verification["no_write_harness"] is True
    assert evaluation.acceptance == {
        "sandbox_only": True,
        "vault_tree_unchanged": True,
        "no_write_delete_move_tools": True,
        "unknown_tools_reviewed": True,
        "protected_paths_declared": True,
        "provenance_policy_ready": True,
        "local_embedding_policy": True,
        "derived_storage_declared": True,
    }
    assert evaluation.verification["status"] == "passed"


def test_build_indexing_spike_evaluation_flags_remote_ollama(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "https://example.invalid:11434")
    evaluation = build_indexing_spike_evaluation(candidate_record=candidate_record(), sandbox_vault=make_sandbox(tmp_path))

    assert evaluation.acceptance["local_embedding_policy"] is False
    assert evaluation.verification["status"] == "needs-review"


def test_obsidian_indexing_spike_cli_writes_reports(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    sandbox = make_sandbox(tmp_path)
    out_dir = repo / "out" / "reports" / "indexing-spike" / f"pytest-{tmp_path.name}"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    env = os.environ.copy()
    env.pop("OLLAMA_BASE_URL", None)

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_indexing_spike.py"),
            "--candidate-record",
            str(candidate_record()),
            "--sandbox-vault",
            str(sandbox),
            "--out-dir",
            str(out_dir),
            "--query",
            "approval manifest backup verify",
            "--query",
            "wikilinks tagged safety notes",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        cwd=repo,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["status"] == "ok"
    assert payload["verification_status"] == "passed"
    assert Path(payload["json_report"]).is_file()
    assert Path(payload["markdown_report"]).is_file()
    report = json.loads(Path(payload["json_report"]).read_text(encoding="utf-8"))
    assert report["acceptance"]["vault_tree_unchanged"] is True
    assert report["fixed_queries"] == ["approval manifest backup verify", "wikilinks tagged safety notes"]

def test_build_indexing_spike_evaluation_rejects_non_sandbox_vault(tmp_path: Path) -> None:
    not_sandbox = tmp_path / "out" / "not-sandbox-vaults" / "indexing-case"
    not_sandbox.mkdir(parents=True)
    (not_sandbox / "note.md").write_text("# Not sandbox\n", encoding="utf-8")

    with pytest.raises(GuardrailError, match="out/sandbox-vaults"):
        build_indexing_spike_evaluation(candidate_record=candidate_record(), sandbox_vault=not_sandbox)


def test_safe_indexing_report_dir_rejects_paths_outside_reports_root(tmp_path: Path) -> None:
    with pytest.raises(GuardrailError, match="out/reports/indexing-spike"):
        safe_indexing_report_dir(tmp_path / "reports")


def test_safe_indexing_report_dir_rejects_live_vault_when_present() -> None:
    live_vault = Path("/home/hermesadmin/Obsidian")
    if not live_vault.exists():
        pytest.skip("live vault path is not present in this environment")

    with pytest.raises(GuardrailError, match="live vault"):
        safe_indexing_report_dir(live_vault / "out" / "reports" / "indexing-spike")



def test_build_indexing_spike_evaluation_rejects_marker_shaped_sandbox_outside_repo(tmp_path: Path) -> None:
    outside = tmp_path / "out" / "sandbox-vaults" / "indexing-case"
    outside.mkdir(parents=True)
    (outside / "note.md").write_text("# Outside marker-shaped sandbox\n", encoding="utf-8")

    with pytest.raises(GuardrailError, match="must live under"):
        build_indexing_spike_evaluation(candidate_record=candidate_record(), sandbox_vault=outside)


def test_safe_indexing_report_dir_rejects_marker_shaped_reports_outside_repo(tmp_path: Path) -> None:
    outside = tmp_path / "out" / "reports" / "indexing-spike"

    with pytest.raises(GuardrailError, match="must live under"):
        safe_indexing_report_dir(outside)


def test_load_indexing_candidate_record_rejects_remote_allowed_embedding_url(tmp_path: Path) -> None:
    bad = json.loads(candidate_record().read_text(encoding="utf-8"))
    bad["embedding_policy"]["allowed_base_urls"] = ["https://remote.example.invalid:11434"]
    bad_path = tmp_path / "remote-embedding-indexer.json"
    bad_path.write_text(json.dumps(bad), encoding="utf-8")

    with pytest.raises(GuardrailError, match="localhost|loopback|local"):
        load_indexing_candidate_record(bad_path)
