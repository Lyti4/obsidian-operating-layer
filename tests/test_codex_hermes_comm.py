import importlib.util
import json
from pathlib import Path


def _load_tool():
    path = Path(__file__).resolve().parents[1] / "tools" / "codex_hermes_comm.py"
    spec = importlib.util.spec_from_file_location("codex_hermes_comm", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_rights_for_review_are_read_only() -> None:
    tool = _load_tool()
    rights = tool.default_rights("review")

    assert rights["repo_read"] is True
    assert rights["repo_write"] is False
    assert rights["live_vault_mutation"] is False
    assert rights["auth_profile_mutation"] is False
    assert rights["service_restart_deploy_cron_network"] is False
    assert "secrets" in rights["secrets_policy"].lower()


def test_default_rights_for_implementation_are_repo_scoped_only() -> None:
    tool = _load_tool()
    rights = tool.default_rights("implementation")

    assert rights["repo_read"] is True
    assert rights["repo_write"] is True
    assert "/home/hermesadmin/work/obsidian-operating-layer" in rights["repo_write_boundary"]
    assert rights["live_vault_mutation"] is False
    assert rights["auth_profile_mutation"] is False
    assert rights["service_restart_deploy_cron_network"] is False


def test_classify_report_requires_hermes_verification_for_changes() -> None:
    tool = _load_tool()
    action, reply = tool.classify_report({"status": "ok", "changed_files": ["tools/x.py"], "tests": ["pytest"]})

    assert action == "ack_changes_pending_hermes_verification"
    assert any("verify" in line.lower() for line in reply)


def test_role_policy_json_has_gated_rights() -> None:
    policy = json.loads(Path("/home/hermesadmin/.codex-hermes/docs/ROLE_POLICY.json").read_text(encoding="utf-8"))

    assert policy["roles"]["hermes"]["role"] == "orchestrator_acceptance_owner"
    assert policy["roles"]["codex"]["role"] == "bounded_implementation_and_review_worker"
    rights = policy["rights"]
    assert "forbidden" in rights["live_vault_mutation"]
    assert "forbidden" in rights["auth_profile_mutation"]
    assert "forbidden" in rights["service_restart_deploy_cron_network"]


def test_invalid_packet_id_is_rejected() -> None:
    tool = _load_tool()

    try:
        tool.safe_id("../escape", "fallback")
    except ValueError as exc:
        assert "id must match" in str(exc)
    else:
        raise AssertionError("unsafe id was accepted")


def test_safe_write_refuses_symlink(tmp_path: Path) -> None:
    tool = _load_tool()
    target = tmp_path / "target.txt"
    link = tmp_path / "link.txt"
    target.write_text("old", encoding="utf-8")
    link.symlink_to(target)

    try:
        tool.safe_write_text(link, "new")
    except ValueError as exc:
        assert "symlink" in str(exc)
    else:
        raise AssertionError("symlink write was accepted")
    assert target.read_text(encoding="utf-8") == "old"



def _load_runner():
    path = Path(__file__).resolve().parents[1] / "tools" / "hermes_codex_run.py"
    spec = importlib.util.spec_from_file_location("hermes_codex_run", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_codex_native_runner_scrubs_secret_env(monkeypatch) -> None:
    runner = _load_runner()
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_secret")

    env = runner.scrubbed_env()

    assert "OPENAI_API_KEY" not in env
    assert "GITHUB_TOKEN" not in env
    assert env["CODEX_HOME"] == "/home/hermesadmin/.codex"


def test_codex_native_runner_rejects_bad_task_id(tmp_path) -> None:
    runner = _load_runner()
    task = tmp_path / "bad.json"
    task.write_text('{"schema":"codex_task.v1","task_id":"../bad","mode":"review"}', encoding="utf-8")

    try:
        runner.load_task(task)
    except ValueError as exc:
        assert "task_id" in str(exc)
    else:
        raise AssertionError("unsafe task id was accepted")


def test_codex_schemas_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    task_schema = json.loads((root / "schemas/codex_task.v1.json").read_text(encoding="utf-8"))
    report_schema = json.loads((root / "schemas/codex_report.v1.json").read_text(encoding="utf-8"))

    assert task_schema["$id"] == "codex_task.v1"
    assert report_schema["$id"] == "codex_report.v1"
    assert "mode" in task_schema["required"]
    assert "commands_run" in report_schema["required"]



def test_review_snapshot_detects_content_change_with_same_git_status(tmp_path) -> None:
    runner = _load_runner()
    import subprocess

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("base", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=tmp_path, check=True)

    tracked.write_text("dirty-one", encoding="utf-8")
    before_status = runner.git_status(tmp_path)
    before_snapshot = runner.repo_content_snapshot(tmp_path)
    tracked.write_text("dirty-two", encoding="utf-8")
    after_status = runner.git_status(tmp_path)
    after_snapshot = runner.repo_content_snapshot(tmp_path)

    assert before_status == after_status
    assert runner.snapshot_delta(before_snapshot, after_snapshot) == ["tracked.txt"]


def test_generated_codex_task_packet_matches_v1_shape(tmp_path) -> None:
    tool = _load_tool()

    class Args:
        id = "pytest-generated-review-task"
        type = "review"
        scope = None
        instructions = "Review generated task packet shape only."
        review_only = True

    path = tool.create_task(Args())
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["schema"] == "codex_task.v1"
    assert payload["task_id"] == Args.id
    assert payload["mode"] == "review"
    assert payload["repo"] == "/home/hermesadmin/work/obsidian-operating-layer"
    assert isinstance(payload["instructions"], list)
    assert isinstance(payload["scope"], dict)
    assert "verification" in payload
    assert "outputs" in payload
    # Runner must accept the packet shape it receives from the channel helper.
    runner = _load_runner()
    assert runner.load_task(path)["task_id"] == Args.id


def test_codex_native_runner_defaults_to_workspace_write() -> None:
    runner = _load_runner()
    parser = runner.build_arg_parser()

    args = parser.parse_args(["--mode", "review", "--task", "task.json"])

    assert args.sandbox == "workspace-write"
    assert args.allow_danger_full_access is False


def test_codex_native_runner_requires_explicit_danger_full_access() -> None:
    runner = _load_runner()

    try:
        runner.validate_sandbox_policy("danger-full-access", allow_danger_full_access=False)
    except ValueError as exc:
        assert "--allow-danger-full-access" in str(exc)
    else:
        raise AssertionError("danger-full-access was accepted without explicit operator flag")

    runner.validate_sandbox_policy("danger-full-access", allow_danger_full_access=True)


def test_codex_native_runner_ingests_inline_report(tmp_path, monkeypatch) -> None:
    runner = _load_runner()
    inbox = tmp_path / "hermes-inbox"
    inbox.mkdir()
    monkeypatch.setattr(runner, "HERMES_INBOX", inbox)
    last_message = tmp_path / "last-message.md"
    last_message.write_text(
        json.dumps(
            {
                "schema": "codex_report.v1",
                "id": "inline-report",
                "task_id": "inline-task",
                "status": "blocked",
                "mode": "review",
                "summary": "blocked",
                "changed_files": [],
                "commands_run": [],
            }
        ),
        encoding="utf-8",
    )

    path = runner.ingest_inline_codex_report({"task_id": "inline-task"}, last_message)

    assert path == inbox / "inline-report.report.json"
    assert json.loads(path.read_text(encoding="utf-8"))["task_id"] == "inline-task"
    assert (inbox / "latest.json").exists()


def test_codex_native_runner_writes_blocked_report_on_timeout(tmp_path, monkeypatch) -> None:
    runner = _load_runner()
    import subprocess
    import sys

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    task = tmp_path / "task.json"
    task.write_text(
        json.dumps(
            {
                "schema": "codex_task.v1",
                "task_id": "timeout-task",
                "mode": "review",
                "repo": str(repo),
                "objective": "timeout regression",
                "scope": {},
                "verification": [],
                "outputs": {},
            }
        ),
        encoding="utf-8",
    )
    comm = tmp_path / "comm"
    monkeypatch.setattr(runner, "HOME", tmp_path)
    monkeypatch.setattr(runner, "DEFAULT_REPO", repo)
    monkeypatch.setattr(runner, "COMM", comm)
    monkeypatch.setattr(runner, "CODEX_INBOX", comm / "codex-inbox")
    monkeypatch.setattr(runner, "HERMES_INBOX", comm / "hermes-inbox")
    monkeypatch.setattr(runner, "PROCESSING", comm / "processing")
    monkeypatch.setattr(runner, "DONE", comm / "done")
    monkeypatch.setattr(runner, "FAILED", comm / "failed")

    real_run = runner.subprocess.run

    def fake_run(*args, **kwargs):
        cmd = args[0]
        if isinstance(cmd, list) and cmd and cmd[0] == "codex":
            raise subprocess.TimeoutExpired(cmd=cmd, timeout=kwargs.get("timeout"), output="partial output")
        return real_run(*args, **kwargs)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "hermes_codex_run.py",
            "--repo",
            str(repo),
            "--mode",
            "review",
            "--task",
            str(task),
            "--codex-timeout-seconds",
            "1",
        ],
    )

    rc = runner.main()

    assert rc == 124
    reports = sorted((comm / "hermes-inbox").glob("timeout-task.wrapper-*.report.json"))
    assert len(reports) == 1
    report = json.loads(reports[0].read_text())
    assert report["status"] == "blocked"
    assert "timed out" in report["summary"]
    assert (comm / "state" / "timeout-task.codex-output.log").read_text() == "partial output"


def test_codex_native_runner_blocks_success_without_report(tmp_path, monkeypatch) -> None:
    runner = _load_runner()
    import subprocess
    import sys

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    task = tmp_path / "task.json"
    task.write_text(
        json.dumps(
            {
                "schema": "codex_task.v1",
                "task_id": "missing-report-task",
                "mode": "review",
                "repo": str(repo),
                "objective": "missing report regression",
                "scope": {},
                "verification": [],
                "outputs": {},
            }
        ),
        encoding="utf-8",
    )
    comm = tmp_path / "comm"
    monkeypatch.setattr(runner, "HOME", tmp_path)
    monkeypatch.setattr(runner, "DEFAULT_REPO", repo)
    monkeypatch.setattr(runner, "COMM", comm)
    monkeypatch.setattr(runner, "CODEX_INBOX", comm / "codex-inbox")
    monkeypatch.setattr(runner, "HERMES_INBOX", comm / "hermes-inbox")
    monkeypatch.setattr(runner, "PROCESSING", comm / "processing")
    monkeypatch.setattr(runner, "DONE", comm / "done")
    monkeypatch.setattr(runner, "FAILED", comm / "failed")

    real_run = runner.subprocess.run

    def fake_run(*args, **kwargs):
        cmd = args[0]
        if isinstance(cmd, list) and cmd and cmd[0] == "codex":
            return subprocess.CompletedProcess(cmd, 0, stdout="codex exited without report\n")
        return real_run(*args, **kwargs)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "hermes_codex_run.py",
            "--repo",
            str(repo),
            "--mode",
            "review",
            "--task",
            str(task),
        ],
    )

    rc = runner.main()

    assert rc == 3
    reports = sorted((comm / "hermes-inbox").glob("missing-report-task.wrapper-*.report.json"))
    assert len(reports) == 1
    report = json.loads(reports[0].read_text())
    assert report["status"] == "blocked"
    assert "did not produce codex_report.v1" in report["summary"]
    assert "missing codex_report.v1 report" in report["blockers"]
