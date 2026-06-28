from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .guardrails import DEFAULT_EXCLUDED_DIRS, GuardrailError, normalize_vault_root, write_json

SAFE_JOB_KINDS = {"observe", "index", "report"}
QUEUE_STATUSES = ("pending", "running", "done", "failed", "cancelled")
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def isoformat_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc_timestamp(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GuardrailError(f"Invalid timestamp: {value}") from exc


def controlled_queue_dirs(queue_root: str | Path) -> dict[str, Path]:
    root = Path(queue_root).expanduser().resolve()
    dirs = {status: root / status for status in QUEUE_STATUSES}
    dirs["reports"] = root / "reports"
    dirs["audit"] = root / "audit"
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs


def _status_path(queue_root: str | Path, status: str, task_id: str) -> Path:
    if status not in QUEUE_STATUSES:
        raise GuardrailError(f"Unknown queue status: {status}")
    return controlled_queue_dirs(queue_root)[status] / f"{task_id}.json"


def _safe_task_id(kind: str, created_at: datetime) -> str:
    stamp = created_at.astimezone(timezone.utc).strftime("%Y%m%d-%H%M%SZ")
    return f"obslayer-{stamp}-{kind}"


def _audit_entry(from_status: str | None, to_status: str, worker: str, note: str, now: datetime) -> dict[str, Any]:
    return {
        "from_status": from_status,
        "to_status": to_status,
        "worker": worker,
        "timestamp": isoformat_z(now),
        "note": note,
    }


def _write_job(queue_root: str | Path, job: dict[str, Any]) -> Path:
    status = str(job.get("status", ""))
    task_id = str(job.get("task_id", ""))
    if not task_id:
        raise GuardrailError("Controlled autonomy job requires task_id")
    path = _status_path(queue_root, status, task_id)
    write_json(path, job)
    return path


def create_controlled_job(
    *,
    queue_root: str | Path,
    kind: str,
    vault_root: str | Path,
    task_id: str | None = None,
    inputs: dict[str, Any] | None = None,
    priority: int = 50,
    schedule_label: str = "manual",
    now: datetime | None = None,
) -> tuple[dict[str, Any], Path]:
    if kind not in SAFE_JOB_KINDS:
        raise GuardrailError(f"Controlled autonomy only supports read-only observe/index/report jobs, got: {kind}")
    created = now or utc_now()
    root = normalize_vault_root(vault_root)
    dirs = controlled_queue_dirs(queue_root)
    job_id = task_id or _safe_task_id(kind, created)
    if controlled_job_exists(queue_root, job_id):
        raise GuardrailError(f"Controlled autonomy job already exists: {job_id}")
    report_json = dirs["reports"] / f"{job_id}.report.json"
    report_md = dirs["reports"] / f"{job_id}.report.md"
    job = {
        "task_id": job_id,
        "created_at": isoformat_z(created),
        "updated_at": isoformat_z(created),
        "status": "pending",
        "worker": f"{kind}-worker",
        "kind": kind,
        "priority": priority,
        "vault_root": str(root),
        "vault_mode": "read-only-live",
        "capabilities": ["read", "search", "index", "report"] if kind == "index" else ["read", kind],
        "write_policy": "proposal_only",
        "schedule": {
            "label": schedule_label,
            "enabled": False,
            "note": "Recorded scheduled intent only; no cron/systemd/gateway scheduler is installed by this tool.",
        },
        "inputs": inputs or {},
        "outputs": {
            "report_json": str(report_json),
            "report_markdown": str(report_md),
            "proposal": None,
        },
        "limits": {
            "timeout_seconds": 600,
            "max_files": 1000,
            "max_output_bytes": 5_000_000,
        },
        "safety": {
            "protected_paths_excluded": True,
            "direct_write_enabled": False,
            "requires_manifest_for_apply": True,
            "live_apply_allowed": False,
        },
        "attempts": 0,
        "max_attempts": 3,
        "depends_on": [],
        "labels": ["controlled-autonomy", "dry-run-default", "read-only"],
        "audit": [_audit_entry(None, "pending", f"{kind}-worker", "created controlled autonomy job", created)],
    }
    return job, _write_job(queue_root, job)


def load_controlled_job(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).expanduser().resolve().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise GuardrailError(f"Controlled autonomy job must be a JSON object: {path}")
    return payload


def find_controlled_job(queue_root: str | Path, task_id: str) -> tuple[dict[str, Any], Path]:
    controlled_queue_dirs(queue_root)
    for status in QUEUE_STATUSES:
        path = _status_path(queue_root, status, task_id)
        if path.exists():
            return load_controlled_job(path), path
    raise GuardrailError(f"Controlled autonomy job not found: {task_id}")


def controlled_job_exists(queue_root: str | Path, task_id: str) -> bool:
    try:
        find_controlled_job(queue_root, task_id)
    except GuardrailError:
        return False
    return True


def list_controlled_jobs(queue_root: str | Path) -> list[dict[str, Any]]:
    dirs = controlled_queue_dirs(queue_root)
    jobs: list[dict[str, Any]] = []
    for status in QUEUE_STATUSES:
        for path in sorted(dirs[status].glob("*.json")):
            jobs.append(load_controlled_job(path))
    return sorted(jobs, key=lambda item: (str(item.get("created_at", "")), str(item.get("task_id", ""))))


def move_controlled_job(
    queue_root: str | Path,
    task_id: str,
    to_status: str,
    note: str,
    now: datetime | None = None,
) -> tuple[dict[str, Any], Path]:
    if to_status not in QUEUE_STATUSES:
        raise GuardrailError(f"Unknown queue status: {to_status}")
    timestamp = now or utc_now()
    job, old_path = find_controlled_job(queue_root, task_id)
    from_status = str(job.get("status", ""))
    job["status"] = to_status
    job["updated_at"] = isoformat_z(timestamp)
    if to_status == "running" and not job.get("started_at"):
        job["started_at"] = isoformat_z(timestamp)
    if to_status in {"done", "failed", "cancelled"}:
        job["completed_at"] = isoformat_z(timestamp)
    job.setdefault("audit", []).append(_audit_entry(from_status, to_status, str(job.get("worker", "")), note, timestamp))
    new_path = _write_job(queue_root, job)
    if old_path != new_path and old_path.exists():
        old_path.unlink()
    return job, new_path


def _is_excluded(rel: Path) -> bool:
    return any(part in DEFAULT_EXCLUDED_DIRS for part in rel.parts)


def build_read_only_index(vault_root: str | Path, max_files: int = 1000) -> dict[str, Any]:
    root = normalize_vault_root(vault_root)
    markdown_files = 0
    sample_notes: list[str] = []
    wikilinks: dict[str, int] = {}
    frontmatter_files = 0
    skipped_excluded_dirs: set[str] = set()

    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root)
        if _is_excluded(rel):
            if rel.parts:
                skipped_excluded_dirs.add(rel.parts[0])
            continue
        markdown_files += 1
        if markdown_files > max_files:
            break
        rel_str = rel.as_posix()
        if len(sample_notes) < 20:
            sample_notes.append(rel_str)
        text = path.read_text(encoding="utf-8", errors="replace")
        if text.startswith("---\n"):
            frontmatter_files += 1
        for match in WIKILINK_RE.findall(text):
            target = match.split("|", 1)[0].strip()
            if target:
                wikilinks[target] = wikilinks.get(target, 0) + 1

    return {
        "vault_root": str(root),
        "markdown_files": min(markdown_files, max_files),
        "truncated": markdown_files > max_files,
        "sample_notes": sample_notes,
        "frontmatter_files": frontmatter_files,
        "wikilink_count": sum(wikilinks.values()),
        "top_wikilinks": dict(sorted(wikilinks.items(), key=lambda item: (-item[1], item[0]))[:20]),
        "excluded_dirs": list(DEFAULT_EXCLUDED_DIRS),
        "skipped_excluded_dirs": sorted(skipped_excluded_dirs),
    }


def render_job_report(job: dict[str, Any], result: dict[str, Any]) -> str:
    mutation = result["mutation_boundary"]
    lines = [
        "# Controlled Autonomy Job Report",
        "",
        f"- task_id: `{job['task_id']}`",
        f"- worker: `{job['worker']}`",
        f"- kind: `{job['kind']}`",
        f"- status: `{result['status']}`",
        f"- vault_root: `{job['vault_root']}`",
        f"- direct_write_enabled: `{mutation['direct_write_enabled']}`",
        f"- approval_required_for_apply: `{mutation['approval_required_for_apply']}`",
        f"- proposed_targets: `{mutation['proposed_targets']}`",
        f"- applied_targets: `{mutation['applied_targets']}`",
        f"- apply_status: `{mutation['apply_status']}`",
        "",
        "## Read-only index",
        "",
        f"- markdown_files: `{result['read_only_index']['markdown_files']}`",
        f"- wikilink_count: `{result['read_only_index']['wikilink_count']}`",
        f"- frontmatter_files: `{result['read_only_index']['frontmatter_files']}`",
        "",
        "## Rollback evidence",
        "",
        f"- backup_dir: `{result['rollback_evidence']['backup_dir']}`",
        f"- note: {result['rollback_evidence']['note']}",
        "",
    ]
    return "\n".join(lines)


def run_controlled_job(queue_root: str | Path, task_id: str, now: datetime | None = None) -> tuple[dict[str, Any], Path]:
    timestamp = now or utc_now()
    job, _ = find_controlled_job(queue_root, task_id)
    if job.get("status") != "pending":
        raise GuardrailError(f"Controlled autonomy job must be pending before run, got: {job.get('status')}")
    running_job, _ = move_controlled_job(queue_root, task_id, "running", "claimed for explicit manual dry-run execution", timestamp)
    kind = str(running_job.get("kind", ""))
    if kind not in SAFE_JOB_KINDS:
        move_controlled_job(queue_root, task_id, "failed", "unsafe controlled autonomy kind refused", timestamp)
        raise GuardrailError(f"Controlled autonomy job kind is not read-only safe: {kind}")

    read_only_index = build_read_only_index(running_job["vault_root"], int(running_job.get("limits", {}).get("max_files", 1000)))
    result = {
        "status": "succeeded",
        "executed_at": isoformat_z(timestamp),
        "task_id": running_job["task_id"],
        "kind": kind,
        "read_only_index": read_only_index,
        "mutation_boundary": {
            "direct_write_enabled": False,
            "approval_required_for_apply": True,
            "live_mutation_attempted": False,
            "apply_status": "not-run",
            "proposed_targets": 0,
            "applied_targets": 0,
        },
        "rollback_evidence": {
            "backup_dir": None,
            "note": "No live apply executed; rollback evidence is only available from approved apply results.",
        },
    }
    outputs = running_job["outputs"]
    report_json = Path(outputs["report_json"]).expanduser().resolve()
    report_md = Path(outputs["report_markdown"]).expanduser().resolve()
    write_json(report_json, result)
    report_md.write_text(render_job_report(running_job, result), encoding="utf-8")

    done_job, done_path = move_controlled_job(queue_root, task_id, "done", "completed read-only controlled autonomy job", timestamp)
    done_job["result"] = result
    done_job["outputs"] = outputs
    done_job["updated_at"] = isoformat_z(timestamp)
    done_path = _write_job(queue_root, done_job)
    return done_job, done_path


def cleanup_stale_running_jobs(
    queue_root: str | Path,
    *,
    older_than_seconds: int,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    if older_than_seconds <= 0:
        raise GuardrailError("older_than_seconds must be positive")
    timestamp = now or utc_now()
    dirs = controlled_queue_dirs(queue_root)
    cleaned: list[dict[str, Any]] = []
    for path in sorted(dirs["running"].glob("*.json")):
        job = load_controlled_job(path)
        raw_started = str(job.get("started_at") or job.get("updated_at") or job.get("created_at") or "")
        if not raw_started:
            continue
        age = (timestamp - parse_utc_timestamp(raw_started)).total_seconds()
        if age > older_than_seconds:
            failed_job, _ = move_controlled_job(
                queue_root,
                str(job["task_id"]),
                "failed",
                f"cleaned up stale running job after {int(age)} seconds",
                timestamp,
            )
            failed_job["failure_reason"] = "stale-running-cleanup"
            failed_job["updated_at"] = isoformat_z(timestamp)
            _write_job(queue_root, failed_job)
            cleaned.append(failed_job)
    return cleaned


def _load_apply_results(paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for path in paths:
        payload = json.loads(Path(path).expanduser().resolve().read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise GuardrailError(f"Apply result must be a JSON object: {path}")
        payload["_source_path"] = str(Path(path).expanduser().resolve())
        results.append(payload)
    return results


def build_acceptance_report(queue_root: str | Path, apply_result_paths: Iterable[str | Path] = ()) -> dict[str, Any]:
    jobs = list_controlled_jobs(queue_root)
    apply_results = _load_apply_results(apply_result_paths)
    status_counts: dict[str, int] = {}
    for job in jobs:
        status = str(job.get("status", "unknown"))
        status_counts[status] = status_counts.get(status, 0) + 1

    applied_targets = 0
    dry_run_results = 0
    rollback_evidence: list[dict[str, Any]] = []
    for result in apply_results:
        status = str(result.get("status", ""))
        if status == "applied":
            applied = result.get("applied", [])
            applied_targets += len(applied) if isinstance(applied, list) else 0
            rollback_evidence.append(
                {
                    "source": result.get("_source_path"),
                    "backup_dir": result.get("backup_dir"),
                    "applied": applied,
                }
            )
        elif status == "dry-run":
            dry_run_results += 1

    proposed_targets = 0
    for job in jobs:
        raw_result = job.get("result")
        result = raw_result if isinstance(raw_result, dict) else {}
        raw_mutation = result.get("mutation_boundary")
        mutation = raw_mutation if isinstance(raw_mutation, dict) else {}
        proposed_targets += int(mutation.get("proposed_targets", 0) or 0)

    return {
        "queue_root": str(Path(queue_root).expanduser().resolve()),
        "generated_at": isoformat_z(utc_now()),
        "job_counts": status_counts,
        "jobs": [_acceptance_job_summary(job) for job in jobs],
        "mutation_summary": {
            "proposed_targets": proposed_targets,
            "applied_targets": applied_targets,
            "dry_run_apply_results": dry_run_results,
            "live_apply_results": sum(1 for result in apply_results if result.get("status") == "applied"),
            "approval_gate": "explicit approval manifest required before any live apply",
        },
        "rollback_evidence": rollback_evidence,
    }


def _acceptance_job_summary(job: dict[str, Any]) -> dict[str, Any]:
    raw_outputs = job.get("outputs")
    outputs = raw_outputs if isinstance(raw_outputs, dict) else {}
    return {
        "task_id": job.get("task_id"),
        "status": job.get("status"),
        "worker": job.get("worker"),
        "kind": job.get("kind"),
        "report": outputs.get("report_markdown"),
    }


def acceptance_report_to_markdown(report: dict[str, Any]) -> str:
    mutation = report["mutation_summary"]
    lines = [
        "# Controlled Autonomy Acceptance Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- queue_root: `{report['queue_root']}`",
        f"- proposed_targets: `{mutation['proposed_targets']}`",
        f"- applied_targets: `{mutation['applied_targets']}`",
        f"- dry_run_apply_results: `{mutation['dry_run_apply_results']}`",
        f"- live_apply_results: `{mutation['live_apply_results']}`",
        f"- approval_gate: {mutation['approval_gate']}",
        "",
        "## Jobs",
        "",
    ]
    for job in report["jobs"]:
        lines.append(f"- `{job['task_id']}` / `{job['kind']}` / `{job['status']}` / report `{job['report']}`")
    lines.extend(["", "## Rollback evidence", ""])
    if report["rollback_evidence"]:
        for item in report["rollback_evidence"]:
            lines.append(f"- source `{item['source']}` backup_dir `{item['backup_dir']}` applied `{len(item.get('applied') or [])}`")
    else:
        lines.append("- No live apply results attached; no rollback backup was created by controlled autonomy.")
    lines.append("")
    return "\n".join(lines)


def write_acceptance_report(
    *,
    queue_root: str | Path,
    markdown_out: str | Path,
    json_out: str | Path | None = None,
    apply_result_paths: Iterable[str | Path] = (),
) -> tuple[Path, Path | None, dict[str, Any]]:
    report = build_acceptance_report(queue_root, apply_result_paths)
    md_path = Path(markdown_out).expanduser().resolve()
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(acceptance_report_to_markdown(report), encoding="utf-8")
    json_path = Path(json_out).expanduser().resolve() if json_out else None
    if json_path:
        write_json(json_path, report)
    return md_path, json_path, report
