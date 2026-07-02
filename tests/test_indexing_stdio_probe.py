from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _stdio_probe_command(
    repo: Path,
    run_name: str,
    *,
    extra_args: list[str] | None = None,
    live_vault_root: Path | None = None,
) -> tuple[list[str], Path, Path]:
    sandbox = repo / "out" / "sandbox-vaults" / run_name
    derived = repo / "out" / "external-indexing-spike" / run_name
    report_root = repo / "out" / "reports" / "external-indexing-spike" / run_name
    for path in (sandbox, derived, report_root):
        if path.exists():
            shutil.rmtree(path)
    sandbox.mkdir(parents=True)
    (sandbox / "Notes").mkdir()
    (sandbox / "Notes" / "Safety.md").write_text("# Safety\nNo live mutation\n", encoding="utf-8")

    command = [
        sys.executable,
        str(repo / "tools" / "obsidian_indexing_stdio_probe.py"),
        "--sandbox-vault",
        str(sandbox),
        "--derived-root",
        str(derived),
        "--report-root",
        str(report_root),
        "--raw-report",
        str(report_root / "raw" / "transcript.json"),
        "--sanitized-report",
        str(report_root / "sanitized-transcript.json"),
        "--command",
        sys.executable,
        "--command",
        str(repo / "tests" / "fixtures" / "fake_jsonline_mcp_server.py"),
        "--query",
        "safety boundary",
        "--timeout-seconds",
        "1",
    ]
    if live_vault_root is not None:
        command.extend(["--live-vault-root", str(live_vault_root)])
    if extra_args:
        command.extend(extra_args)
    return command, report_root, sandbox


def test_stdio_probe_runs_fake_mcp_through_sanitizing_wrapper(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    run_name = f"stdio-probe-pytest-{tmp_path.name}"
    command, report_root, sandbox = _stdio_probe_command(repo, run_name)
    derived = repo / "out" / "external-indexing-spike" / run_name

    result = subprocess.run(command, cwd=repo, text=True, capture_output=True, check=True)
    summary = json.loads(result.stdout)
    assert summary["status"] == "ok"
    assert summary["calls"] >= 5
    assert "process_spec" not in summary
    assert str(sandbox) not in result.stdout
    assert str(derived) not in result.stdout

    raw = json.loads((report_root / "raw" / "transcript.json").read_text(encoding="utf-8"))
    sanitized = json.loads((report_root / "sanitized-transcript.json").read_text(encoding="utf-8"))
    assert len(raw["calls"]) == summary["calls"]
    assert sanitized["calls"][0]["kind"] == "list_tools"
    assert sanitized["calls"][0]["tools"] == ["search_notes", "read_note", "index_vault", "index_status"]
    assert any(call.get("tool") == "read_note" for call in sanitized["calls"])
    assert str(sandbox) not in json.dumps(sanitized, ensure_ascii=False)
    status = next(call for call in sanitized["calls"] if call.get("tool") == "index_status")
    assert status["payload"]["inherited_openai_api_key"] is False
    assert status["payload"]["inherited_gh_token"] is False


def test_stdio_probe_does_not_inherit_secret_parent_env(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    command, report_root, _sandbox = _stdio_probe_command(repo, f"stdio-probe-env-{tmp_path.name}")
    env = os.environ.copy()
    env["OPENAI_API_KEY"] = "parent-secret"
    env["GH_TOKEN"] = "parent-token"

    result = subprocess.run(command, cwd=repo, text=True, capture_output=True, env=env, check=True)

    assert "parent-secret" not in result.stdout + result.stderr
    assert "parent-token" not in result.stdout + result.stderr
    sanitized = json.loads((report_root / "sanitized-transcript.json").read_text(encoding="utf-8"))
    status = next(call for call in sanitized["calls"] if call.get("tool") == "index_status")
    assert status["payload"]["inherited_openai_api_key"] is False
    assert status["payload"]["inherited_gh_token"] is False


def test_stdio_probe_does_not_inherit_parent_node_or_npm_paths(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    command, report_root, sandbox = _stdio_probe_command(repo, f"stdio-probe-env-paths-{tmp_path.name}")
    env = os.environ.copy()
    env["NODE_PATH"] = "/home/hermesadmin/Obsidian/node_modules"
    env["npm_config_cache"] = "/home/hermesadmin/Obsidian/.npm-cache"
    env["npm_config_prefix"] = "/tmp/outside-prefix"
    env["PATH"] = f"{sandbox}:{env.get('PATH', '')}"

    subprocess.run(command, cwd=repo, text=True, capture_output=True, env=env, check=True)

    sanitized = json.loads((report_root / "sanitized-transcript.json").read_text(encoding="utf-8"))
    status = next(call for call in sanitized["calls"] if call.get("tool") == "index_status")
    payload = status["payload"]
    assert payload["node_path"] is None
    assert payload["npm_config_cache"] == "<DERIVED_ROOT>/npm-cache"
    assert payload["npm_config_prefix"] == "<DERIVED_ROOT>/npm-prefix"


def test_stdio_probe_child_path_keeps_local_bin_for_project_node_tooling() -> None:
    repo = Path(__file__).resolve().parents[1]
    source = (repo / "tools" / "obsidian_indexing_stdio_probe.py").read_text(encoding="utf-8")

    assert 'SAFE_CHILD_PATH = "/home/hermesadmin/.local/bin:' in source
    assert ":/usr/bin:" in source


def _run_failure(
    repo: Path,
    tmp_path: Path,
    *,
    mode: str | None = None,
    extra_args: list[str] | None = None,
    env_updates: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    run_name = f"stdio-probe-fail-{mode or 'args'}-{tmp_path.name}"
    command, _, _ = _stdio_probe_command(repo, run_name, extra_args=extra_args)
    env = os.environ.copy()
    if mode:
        env["FAKE_MCP_MODE"] = mode
    if env_updates:
        env.update(env_updates)
    return subprocess.run(command, cwd=repo, text=True, capture_output=True, env=env, check=False)


def test_stdio_probe_fails_closed_on_malformed_json(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = _run_failure(repo, tmp_path, mode="malformed-json")
    assert result.returncode == 2
    assert "malformed JSON" in result.stderr


def test_stdio_probe_fails_closed_on_failed_initialize(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = _run_failure(repo, tmp_path, mode="failed-initialize")
    assert result.returncode == 2
    assert "initialize" in result.stderr
    assert "returned error" in result.stderr


def test_stdio_probe_fails_closed_on_bad_initialize_shape(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = _run_failure(repo, tmp_path, mode="bad-initialize")
    assert result.returncode == 2
    assert "protocolVersion" in result.stderr


def test_stdio_probe_detects_live_vault_mutation_attempt(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    live_vault = tmp_path / "live-vault"
    live_vault.mkdir()
    target = live_vault / "mutated.md"
    command, _, _ = _stdio_probe_command(
        repo,
        f"stdio-probe-live-mutation-{tmp_path.name}",
        live_vault_root=live_vault,
    )
    env = os.environ.copy()
    env["FAKE_MCP_MODE"] = "live-vault-mutation"
    env["FAKE_MCP_LIVE_MUTATION_TARGET"] = str(target)

    result = subprocess.run(command, cwd=repo, text=True, capture_output=True, env=env, check=False)

    assert result.returncode == 2
    assert "detected live vault mutation" in result.stderr
    assert target.read_text(encoding="utf-8") == "mutated by fake MCP\n"


def test_stdio_probe_fails_closed_on_extra_or_missing_tools(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    extra = _run_failure(repo, tmp_path, mode="extra-tool")
    assert extra.returncode == 2
    assert "non-allowlisted" in extra.stderr

    missing = _run_failure(repo, tmp_path, mode="missing-tool")
    assert missing.returncode == 2
    assert "missing required" in missing.stderr


def test_stdio_probe_fails_closed_on_tools_list_error(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = _run_failure(repo, tmp_path, mode="failed-tools-list")
    assert result.returncode == 2
    assert "tools/list" in result.stderr
    assert "returned error" in result.stderr


def test_stdio_probe_fails_closed_on_tools_call_error(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = _run_failure(repo, tmp_path, mode="failed-tools-call")
    assert result.returncode == 2
    assert "tools/call" in result.stderr
    assert "returned error" in result.stderr


def test_stdio_probe_reports_failed_status_after_failed_index_vault_report_is_written(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    command, report_root, _sandbox = _stdio_probe_command(repo, f"stdio-probe-index-failed-{tmp_path.name}")
    env = os.environ.copy()
    env["FAKE_MCP_MODE"] = "failed-index-vault"

    result = subprocess.run(command, cwd=repo, text=True, capture_output=True, env=env, check=False)

    assert result.returncode != 0
    summary = json.loads(result.stdout)
    assert summary["status"] == "failed"
    assert summary["calls"] >= 5
    raw = json.loads((report_root / "raw" / "transcript.json").read_text(encoding="utf-8"))
    sanitized = json.loads((report_root / "sanitized-transcript.json").read_text(encoding="utf-8"))
    raw_index_call = next(call for call in raw["calls"] if call.get("tool") == "index_vault")
    sanitized_index_call = next(call for call in sanitized["calls"] if call.get("tool") == "index_vault")
    assert json.loads(raw_index_call["message"]["result"]["content"][0]["text"])["failed"] == 1
    assert sanitized_index_call["payload"]["failed"] == 1


def test_stdio_probe_timeout_is_bounded(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = _run_failure(repo, tmp_path, mode="timeout")
    assert result.returncode == 2
    assert "Timed out" in result.stderr


def test_stdio_probe_timeout_cleans_up_child_process_group(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    pid_file = tmp_path / "child.pid"
    term_file = tmp_path / "child.term"

    result = _run_failure(
        repo,
        tmp_path,
        mode="timeout-with-child",
        env_updates={
            "FAKE_MCP_CHILD_PID_FILE": str(pid_file),
            "FAKE_MCP_CHILD_TERM_FILE": str(term_file),
        },
    )

    assert result.returncode == 2
    assert "Timed out" in result.stderr
    assert pid_file.exists()
    assert term_file.read_text(encoding="utf-8") == "15"


def test_stdio_probe_sanitizes_stderr_tail_on_failure(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = _run_failure(repo, tmp_path, mode="sensitive-stderr-timeout")
    sandbox = repo / "out" / "sandbox-vaults" / f"stdio-probe-fail-sensitive-stderr-timeout-{tmp_path.name}"
    derived = repo / "out" / "external-indexing-spike" / f"stdio-probe-fail-sensitive-stderr-timeout-{tmp_path.name}"

    assert result.returncode == 2
    assert "/home/hermesadmin/Obsidian" not in result.stderr
    assert str(sandbox) not in result.stderr
    assert str(derived) not in result.stderr
    assert "supersecret" not in result.stderr
    assert "<LIVE_VAULT>" in result.stderr
    assert "<SANDBOX_VAULT>" in result.stderr
    assert "<DERIVED_ROOT>" in result.stderr
    assert "<REDACTED_SECRET>" in result.stderr


def test_stdio_probe_sanitizes_jsonrpc_error_body(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = _run_failure(repo, tmp_path, mode="sensitive-tools-call-error")
    sandbox = repo / "out" / "sandbox-vaults" / f"stdio-probe-fail-sensitive-tools-call-error-{tmp_path.name}"
    derived = repo / "out" / "external-indexing-spike" / f"stdio-probe-fail-sensitive-tools-call-error-{tmp_path.name}"

    assert result.returncode == 2
    assert "/home/hermesadmin/Obsidian" not in result.stderr
    assert str(sandbox) not in result.stderr
    assert str(derived) not in result.stderr
    assert "supersecret" not in result.stderr
    assert "<LIVE_VAULT>" in result.stderr
    assert "<SANDBOX_VAULT>" in result.stderr
    assert "<DERIVED_ROOT>" in result.stderr
    assert "<REDACTED_SECRET>" in result.stderr


def test_stdio_probe_rejects_non_dry_run_without_explicit_derived_write_allowance(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = _run_failure(repo, tmp_path, extra_args=["--non-dry-run"])
    assert result.returncode == 2
    assert "without --allow-derived-index-write" in result.stderr


def test_stdio_probe_allows_explicit_sandbox_derived_index_write(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    command, report_root, _sandbox = _stdio_probe_command(
        repo,
        f"stdio-probe-derived-write-{tmp_path.name}",
        extra_args=["--non-dry-run", "--allow-derived-index-write"],
    )

    result = subprocess.run(command, cwd=repo, text=True, capture_output=True, check=True)
    summary = json.loads(result.stdout)
    assert summary["status"] == "ok"
    sanitized = json.loads((report_root / "sanitized-transcript.json").read_text(encoding="utf-8"))
    index_call = next(call for call in sanitized["calls"] if call.get("tool") == "index_vault")
    assert index_call["payload"]["dryRun"] is False

def test_stdio_probe_indexes_paths_file_in_batches_and_skips_protected_paths(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    run_name = f"stdio-probe-batched-paths-{tmp_path.name}"
    command, report_root, sandbox = _stdio_probe_command(repo, run_name)
    derived = repo / "out" / "external-indexing-spike" / run_name
    (sandbox / "Notes" / "Second.md").write_text("# Second\n", encoding="utf-8")
    (sandbox / "_Archive").mkdir()
    (sandbox / "_Archive" / "Skip.md").write_text("# Skip\n", encoding="utf-8")
    paths_file = derived / "paths.json"
    derived.mkdir(parents=True, exist_ok=True)
    paths_file.write_text(
        json.dumps({"paths": ["Notes/Safety.md", "_Archive/Skip.md", "Notes/Second.md"]}),
        encoding="utf-8",
    )
    command.extend(["--paths-file", str(paths_file), "--batch-size", "1"])

    result = subprocess.run(command, cwd=repo, text=True, capture_output=True, check=True)

    summary = json.loads(result.stdout)
    assert summary["status"] == "ok"
    raw = json.loads((report_root / "raw" / "transcript.json").read_text(encoding="utf-8"))
    index_calls = [call for call in raw["calls"] if call.get("tool") == "index_vault"]
    assert [call["batch"]["paths"] for call in index_calls] == [["Notes/Safety.md"], ["Notes/Second.md"]]
    checkpoint = json.loads((derived / "batch-checkpoint.json").read_text(encoding="utf-8"))
    assert checkpoint["requested"] == 3
    assert checkpoint["allowed"] == 2
    assert checkpoint["skipped"] == ["_Archive/Skip.md"]
    assert len(checkpoint["completed_batches"]) == 2

def test_stdio_probe_resumes_paths_file_from_checkpoint_without_reindexing_completed_batch(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    run_name = f"stdio-probe-resume-paths-{tmp_path.name}"
    command, report_root, sandbox = _stdio_probe_command(repo, run_name)
    derived = repo / "out" / "external-indexing-spike" / run_name
    (sandbox / "Notes" / "Second.md").write_text("# Second\n", encoding="utf-8")
    derived.mkdir(parents=True, exist_ok=True)
    paths_file = derived / "paths.json"
    checkpoint_file = derived / "batch-checkpoint.json"
    paths_file.write_text(json.dumps({"paths": ["Notes/Safety.md", "Notes/Second.md"]}), encoding="utf-8")
    checkpoint_file.write_text(
        json.dumps(
            {
                "completed_batches": [
                    {"index": 1, "paths": ["Notes/Safety.md"], "stderr_tail": ""},
                ]
            }
        ),
        encoding="utf-8",
    )
    command.extend(
        [
            "--paths-file",
            str(paths_file),
            "--batch-size",
            "1",
            "--batch-checkpoint",
            str(checkpoint_file),
            "--resume",
        ]
    )

    result = subprocess.run(command, cwd=repo, text=True, capture_output=True, check=True)

    assert json.loads(result.stdout)["status"] == "ok"
    raw = json.loads((report_root / "raw" / "transcript.json").read_text(encoding="utf-8"))
    index_calls = [call for call in raw["calls"] if call.get("tool") == "index_vault"]
    assert [call["batch"]["paths"] for call in index_calls] == [["Notes/Second.md"]]
    checkpoint = json.loads(checkpoint_file.read_text(encoding="utf-8"))
    assert checkpoint["resume"] is True
    assert checkpoint["pending"] == 1
    assert [batch["paths"] for batch in checkpoint["completed_batches"]] == [["Notes/Safety.md"], ["Notes/Second.md"]]

def test_stdio_probe_batched_failed_index_is_not_marked_completed_for_resume(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    run_name = f"stdio-probe-batch-failed-{tmp_path.name}"
    command, report_root, sandbox = _stdio_probe_command(repo, run_name)
    derived = repo / "out" / "external-indexing-spike" / run_name
    paths_file = derived / "paths.json"
    derived.mkdir(parents=True, exist_ok=True)
    paths_file.write_text(json.dumps({"paths": ["Notes/Safety.md"]}), encoding="utf-8")
    command.extend(["--paths-file", str(paths_file), "--batch-size", "1"])
    env = os.environ.copy()
    env["FAKE_MCP_MODE"] = "failed-index-vault"

    result = subprocess.run(command, cwd=repo, text=True, capture_output=True, env=env, check=False)

    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "failed"
    checkpoint = json.loads((derived / "batch-checkpoint.json").read_text(encoding="utf-8"))
    assert checkpoint["completed_batches"] == []
    assert checkpoint["failed_batches"][0]["paths"] == ["Notes/Safety.md"]
    sanitized = json.loads((report_root / "sanitized-transcript.json").read_text(encoding="utf-8"))
    index_call = next(call for call in sanitized["calls"] if call.get("tool") == "index_vault")
    assert index_call["payload"]["failed"] == 1


def test_stdio_probe_rejects_paths_file_outside_derived_root(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    outside_paths = tmp_path / "paths.json"
    outside_paths.write_text(json.dumps({"paths": ["Notes/Safety.md"]}), encoding="utf-8")

    result = _run_failure(repo, tmp_path, extra_args=["--paths-file", str(outside_paths)])

    assert result.returncode == 2
    assert "paths file must live under derived root" in result.stderr
    assert str(outside_paths) not in result.stderr


def test_stdio_probe_rejects_resume_checkpoint_for_different_request(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    run_name = f"stdio-probe-resume-mismatch-{tmp_path.name}"
    command, _report_root, _sandbox = _stdio_probe_command(repo, run_name)
    derived = repo / "out" / "external-indexing-spike" / run_name
    derived.mkdir(parents=True, exist_ok=True)
    paths_file = derived / "paths.json"
    checkpoint_file = derived / "batch-checkpoint.json"
    paths_file.write_text(json.dumps({"paths": ["Notes/Safety.md"]}), encoding="utf-8")
    checkpoint_file.write_text(
        json.dumps({"allowed_paths": ["Notes/Other.md"], "completed_batches": []}),
        encoding="utf-8",
    )
    command.extend(["--paths-file", str(paths_file), "--batch-checkpoint", str(checkpoint_file), "--resume"])

    result = subprocess.run(command, cwd=repo, text=True, capture_output=True, check=False)

    assert result.returncode == 2
    assert "batch checkpoint does not match current request: allowed_paths" in result.stderr
