#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer import (
    GuardrailError,
    cleanup_stale_running_jobs,
    create_controlled_job,
    list_controlled_jobs,
    run_controlled_job,
    write_acceptance_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run explicit, tracked, read-only controlled-autonomy jobs for the Obsidian operating layer."
    )
    parser.add_argument("--queue-root", default="out/queue", help="Local queue root; no scheduler is installed or enabled")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create a pending observe/index/report job")
    create.add_argument("--kind", choices=["observe", "index", "report"], required=True)
    create.add_argument("--vault", default="/home/hermesadmin/Obsidian")
    create.add_argument("--task-id")
    create.add_argument("--schedule-label", default="manual")
    create.add_argument("--priority", type=int, default=50)

    subparsers.add_parser("list", help="List tracked controlled-autonomy jobs")

    run = subparsers.add_parser("run", help="Run one pending job as an explicit manual dry-run/read-only step")
    run.add_argument("--task-id", required=True)

    cleanup = subparsers.add_parser("cleanup", help="Move stale running jobs to failed with audit evidence")
    cleanup.add_argument("--older-than-seconds", type=int, required=True)

    report = subparsers.add_parser("report", help="Write an acceptance report distinguishing proposed vs applied work")
    report.add_argument("--out", required=True, help="Markdown report output path")
    report.add_argument("--json-out", help="Optional JSON report output path")
    report.add_argument("--apply-result", action="append", default=[], help="Optional obsidian_apply.py result JSON")

    args = parser.parse_args()
    queue_root = Path(args.queue_root).expanduser().resolve()

    if args.command == "create":
        job, path = create_controlled_job(
            queue_root=queue_root,
            kind=args.kind,
            vault_root=args.vault,
            task_id=args.task_id,
            schedule_label=args.schedule_label,
            priority=args.priority,
        )
        print(json.dumps({"status": "ok", "task_id": job["task_id"], "job": str(path)}, indent=2, sort_keys=True))
        return 0

    if args.command == "list":
        print(json.dumps({"status": "ok", "jobs": list_controlled_jobs(queue_root)}, indent=2, sort_keys=True))
        return 0

    if args.command == "run":
        job, path = run_controlled_job(queue_root, args.task_id)
        print(
            json.dumps(
                {"status": "ok", "task_id": job["task_id"], "job": str(path), "outputs": job["outputs"]},
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if args.command == "cleanup":
        cleaned = cleanup_stale_running_jobs(queue_root, older_than_seconds=args.older_than_seconds)
        print(json.dumps({"status": "ok", "cleaned": [job["task_id"] for job in cleaned]}, indent=2, sort_keys=True))
        return 0

    if args.command == "report":
        md_path, json_path, payload = write_acceptance_report(
            queue_root=queue_root,
            markdown_out=args.out,
            json_out=args.json_out,
            apply_result_paths=args.apply_result,
        )
        print(
            json.dumps(
                {
                    "status": "ok",
                    "out": str(md_path),
                    "json_out": str(json_path) if json_path else None,
                    "mutation_summary": payload["mutation_summary"],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    raise GuardrailError(f"Unknown command: {args.command}")


def cli() -> int:
    try:
        return main()
    except GuardrailError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
