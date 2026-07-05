#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HOME = Path("/home/hermesadmin")
DEFAULT_REPO = HOME / "work" / "obsidian-operating-layer"
COMM = HOME / ".codex-hermes" / "comm"
CODEX_INBOX = COMM / "codex-inbox"
HERMES_INBOX = COMM / "hermes-inbox"
PROCESSING = COMM / "processing"
DONE = COMM / "done"
FAILED = COMM / "failed"
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SECRET_ENV_RE = re.compile(r"(TOKEN|KEY|SECRET|PASSWORD|COOKIE|CREDENTIAL|DATABASE_URL|AUTH|SESSION)", re.I)
FORBIDDEN_TASK_RE = re.compile(
    r"(live\s+vault|auth|profile|service\s+restart|deploy|cron|network\s+exposure|public\s+posting|paid\s+action)",
    re.I,
)
SECRET_TEXT_PATTERNS = [
    (re.compile(r"Bearer\s+[A-Za-z0-9._~+/-]+=*"), "Bearer [REDACTED]"),
    (re.compile(r"(access_token|refresh_token|id_token|api_key|secret)([\"\'\s:=]+)([^\s\"\']+)", re.I), r"\1\2[REDACTED]"),
    (re.compile(r"sk-[A-Za-z0-9_-]{16,}"), "sk-[REDACTED]"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"), "gh[REDACTED]"),
]


def stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def ensure_dirs() -> None:
    for p in [CODEX_INBOX, HERMES_INBOX, PROCESSING, DONE, FAILED, COMM / "state"]:
        p.mkdir(parents=True, exist_ok=True)


def load_task(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("task must be a JSON object")
    task_id = str(data.get("task_id") or data.get("id") or "")
    if not SAFE_ID.fullmatch(task_id):
        raise ValueError("task_id/id must match [A-Za-z0-9][A-Za-z0-9._-]{0,127}")
    mode = str(data.get("mode") or data.get("type") or "")
    if mode not in {"implementation", "review", "audit", "plan-review"}:
        raise ValueError("mode/type must be implementation, review, audit, or plan-review")
    validate_task_policy(data)
    return data



def validate_task_policy(data: dict[str, Any]) -> None:
    if data.get("schema") == "codex_task.v1":
        required = ["task_id", "mode", "repo", "objective", "scope", "verification", "outputs"]
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(f"codex_task.v1 missing required fields: {', '.join(missing)}")
        if not isinstance(data.get("scope"), dict):
            raise ValueError("codex_task.v1 scope must be an object")
        instructions = data.get("instructions", [])
        if instructions and not isinstance(instructions, list):
            raise ValueError("codex_task.v1 instructions must be an array when present")
    task_text = json.dumps(data, ensure_ascii=False)
    if FORBIDDEN_TASK_RE.search(task_text):
        rights = data.get("rights") if isinstance(data.get("rights"), dict) else {}
        # Mentioning forbidden surfaces as denied rights is normal. Requested permission is not.
        gated_keys = [
            "live_vault_mutation",
            "auth_profile_mutation",
            "service_restart_deploy_cron_network",
            "public_posting",
            "paid_actions",
        ]
        if any(rights.get(key) is True for key in gated_keys):
            raise ValueError("task appears to request gated/forbidden rights")


def tracked_and_untracked_files(repo: Path) -> list[str]:
    commands = [
        ["git", "-C", str(repo), "ls-files"],
        ["git", "-C", str(repo), "ls-files", "--others", "--exclude-standard"],
    ]
    files: set[str] = set()
    for cmd in commands:
        proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
        files.update(line.strip() for line in proc.stdout.splitlines() if line.strip())
    return sorted(files)


def file_digest(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                h.update(chunk)
    except FileNotFoundError:
        return "missing"
    return h.hexdigest()


def repo_content_snapshot(repo: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for rel in tracked_and_untracked_files(repo):
        path = repo / rel
        if path.is_file() and not path.is_symlink():
            snapshot[rel] = file_digest(path)
        elif path.exists():
            snapshot[rel] = f"special:{path.stat().st_mode}"
        else:
            snapshot[rel] = "missing"
    return snapshot


def snapshot_delta(before: dict[str, str], after: dict[str, str]) -> list[str]:
    changed: list[str] = []
    for key in sorted(set(before) | set(after)):
        if before.get(key) != after.get(key):
            changed.append(key)
    return changed

def scrubbed_env() -> dict[str, str]:
    keep = {
        "HOME": str(HOME),
        "USER": "hermesadmin",
        "LOGNAME": "hermesadmin",
        "PATH": os.environ.get("PATH", "/home/hermesadmin/.local/bin:/usr/local/bin:/usr/bin:/bin"),
        "SHELL": "/bin/bash",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "CODEX_HOME": str(HOME / ".codex"),
    }
    return {k: v for k, v in keep.items() if not SECRET_ENV_RE.search(k)}


def sanitize_text(value: str) -> str:
    for pattern, repl in SECRET_TEXT_PATTERNS:
        value = pattern.sub(repl, value)
    return value


def git_status(repo: Path) -> str:
    proc = subprocess.run(["git", "-C", str(repo), "status", "--short"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.stdout



def ingest_inline_codex_report(task: dict[str, Any], last_message: Path) -> Path | None:
    if not last_message.exists():
        return None
    text = last_message.read_text(encoding="utf-8", errors="replace").strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    task_id = str(task.get("task_id") or task.get("id"))
    if not isinstance(payload, dict):
        return None
    if payload.get("schema") != "codex_report.v1" or str(payload.get("task_id")) != task_id:
        return None
    payload.setdefault("requires_hermes_acceptance", True)
    payload.setdefault("safety", "Codex inline report captured by Hermes wrapper; Hermes must verify before acceptance.")
    report_id = str(payload.get("id") or f"{task_id}.codex-inline-{stamp()}")
    if not SAFE_ID.fullmatch(report_id):
        report_id = f"{task_id}.codex-inline-{stamp()}"
    path = HERMES_INBOX / f"{report_id}.report.json"
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(sanitize_text(json.dumps(payload, ensure_ascii=False, indent=2)) + "\n", encoding="utf-8")
    tmp.replace(path)
    (HERMES_INBOX / "latest.json").write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return path

def write_report(
    task: dict[str, Any],
    status: str,
    summary: str,
    mode: str,
    commands: list[str],
    blockers: list[str] | None = None,
    changed_files: list[str] | None = None,
) -> Path:
    ensure_dirs()
    task_id = str(task.get("task_id") or task.get("id"))
    report_id = f"{task_id}.wrapper-{stamp()}"
    payload = {
        "schema": "codex_report.v1",
        "id": report_id,
        "task_id": task_id,
        "created_at": stamp(),
        "from": "codex-wrapper",
        "to": "hermes",
        "channel": "codex-hermes-internal-server",
        "status": status,
        "mode": mode,
        "summary": summary,
        "changed_files": changed_files or [],
        "commands_run": commands,
        "tests": [],
        "blockers": blockers or [],
        "requires_hermes_acceptance": True,
        "safety": "Wrapper-generated report; Hermes must verify before acceptance.",
    }
    path = HERMES_INBOX / f"{report_id}.report.json"
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    (HERMES_INBOX / "latest.json").write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return path



def validate_sandbox_policy(sandbox: str, *, allow_danger_full_access: bool) -> None:
    if sandbox == "danger-full-access" and not allow_danger_full_access:
        raise ValueError("danger-full-access requires --allow-danger-full-access")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hermes-controlled Codex native runner")
    parser.add_argument("--repo", default=str(DEFAULT_REPO))
    parser.add_argument("--mode", choices=["implementation", "review"], required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--profile", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sandbox", default="workspace-write")
    parser.add_argument("--codex-timeout-seconds", type=int, default=900)
    parser.add_argument(
        "--allow-danger-full-access",
        action="store_true",
        help="Require an explicit operator decision before using Codex danger-full-access sandbox.",
    )
    return parser

def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    ensure_dirs()
    repo = Path(args.repo).resolve()
    if repo != DEFAULT_REPO.resolve():
        raise SystemExit(f"refusing repo outside canonical root: {repo}")
    task_path = Path(args.task).expanduser().resolve()
    task = load_task(task_path)
    task_id = str(task.get("task_id") or task.get("id"))
    task_mode = str(task.get("mode") or task.get("type"))
    if args.mode == "review" and task_mode == "implementation":
        raise SystemExit("review runner cannot execute implementation task")
    try:
        validate_sandbox_policy(args.sandbox, allow_danger_full_access=args.allow_danger_full_access)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    processing = PROCESSING / f"{task_id}.task.json"
    if task_path.exists() and task_path.parent == CODEX_INBOX.resolve():
        shutil.copy2(task_path, processing)

    before = git_status(repo)
    before_snapshot = repo_content_snapshot(repo) if args.mode == "review" else {}
    profile = args.profile or ("hermes-review" if args.mode == "review" else "hermes-impl")
    last_message = COMM / "state" / f"{task_id}.last-message.md"
    cmd = [
        "codex",
        "-C",
        str(repo),
        "-s",
        args.sandbox,
        "-a",
        "never",
        "-p",
        profile,
        "exec",
        "-o",
        str(last_message),
        "-",
    ]
    prompt = (
        "You are Codex running under Hermes wrapper. Follow AGENTS.md and the task JSON. "
        "Do not print/read secrets. Do not mutate live vault/auth/services/cron/network. "
        "Write a codex_report.v1 JSON report to ~/.codex-hermes/comm/hermes-inbox/.\n\n"
        + json.dumps(task, ensure_ascii=False, indent=2)
    )
    if args.dry_run:
        report = write_report(
            task,
            "dry-run-ok",
            "Wrapper preflight succeeded; Codex was not invoked.",
            args.mode,
            ["dry-run: " + " ".join(cmd)],
        )
        print(json.dumps({"status": "ok", "dry_run": True, "task_id": task_id, "report": str(report), "cmd": cmd}, ensure_ascii=False))
        return 0

    output_path = COMM / "state" / f"{task_id}.codex-output.log"
    try:
        proc = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=scrubbed_env(),
            cwd=str(repo),
            timeout=args.codex_timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        partial = exc.stdout or ""
        if isinstance(partial, bytes):
            partial = partial.decode(errors="replace")
        output_path.write_text(sanitize_text(str(partial)[-20000:]), encoding="utf-8")
        after = git_status(repo)
        changed = [line.strip() for line in after.splitlines() if line.strip()]
        report = write_report(
            task,
            "blocked",
            f"Codex invocation timed out after {args.codex_timeout_seconds}s; see local wrapper log.",
            args.mode,
            [" ".join(cmd)],
            ["codex invocation timed out"],
            changed,
        )
        shutil.copy2(processing, FAILED / processing.name) if processing.exists() else None
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason": "codex timeout",
                    "timeout_seconds": args.codex_timeout_seconds,
                    "report": str(report),
                    "log": str(output_path),
                },
                ensure_ascii=False,
            )
        )
        return 124
    output_path.write_text(sanitize_text(proc.stdout[-20000:]), encoding="utf-8")
    after = git_status(repo)
    after_snapshot = repo_content_snapshot(repo) if args.mode == "review" else {}
    snapshot_changes = snapshot_delta(before_snapshot, after_snapshot) if args.mode == "review" else []
    changed = [line.strip() for line in after.splitlines() if line.strip()]
    if args.mode == "review" and (after != before or snapshot_changes):
        report = write_report(
            task,
            "failed",
            "Review-only run changed repository status; wrapper marked protocol violation.",
            args.mode,
            [" ".join(cmd)],
            ["review-only changed repository content/status"],
            sorted(set(changed + snapshot_changes)),
        )
        shutil.copy2(processing, FAILED / processing.name) if processing.exists() else None
        print(json.dumps({"status": "failed", "reason": "review-only produced diff", "report": str(report)}, ensure_ascii=False))
        return 2
    if proc.returncode != 0:
        inline_report = ingest_inline_codex_report(task, last_message)
        report = inline_report or write_report(
            task,
            "blocked",
            f"Codex invocation failed with rc={proc.returncode}; see local wrapper log.",
            args.mode,
            [" ".join(cmd)],
            ["codex invocation failed"],
            changed,
        )
        shutil.copy2(processing, FAILED / processing.name) if processing.exists() else None
        print(json.dumps({"status": "blocked", "rc": proc.returncode, "report": str(report), "log": str(output_path)}, ensure_ascii=False))
        return proc.returncode
    inline_report = ingest_inline_codex_report(task, last_message)
    if inline_report is None:
        report = write_report(
            task,
            "blocked",
            "Codex exited successfully but did not produce codex_report.v1; wrapper marked protocol violation.",
            args.mode,
            [" ".join(cmd)],
            ["missing codex_report.v1 report"],
            changed,
        )
        shutil.copy2(processing, FAILED / processing.name) if processing.exists() else None
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason": "missing codex_report.v1 report",
                    "report": str(report),
                    "log": str(output_path),
                },
                ensure_ascii=False,
            )
        )
        return 3
    shutil.copy2(processing, DONE / processing.name) if processing.exists() else None
    print(
        json.dumps(
            {
                "status": "ok",
                "task_id": task_id,
                "before_status": before,
                "after_status": after,
                "inline_report": str(inline_report) if inline_report else None,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
