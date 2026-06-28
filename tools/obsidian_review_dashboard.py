#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from _bootstrap import SRC  # noqa: F401

from obslayer import GuardrailError, load_json, write_json

SAFE_STATUSES = {"proposed", "needs-review", "applied", "rejected"}


def _proposal_id(path: Path, proposal: dict[str, Any]) -> str:
    return str(proposal.get("proposal_id") or proposal.get("id") or proposal.get("source_id") or path.parent.name or path.stem)


def _proposal_status(proposal: dict[str, Any]) -> str:
    raw = str(proposal.get("status") or proposal.get("review_status") or "needs-review")
    return raw if raw in SAFE_STATUSES else "needs-review"


def _proposal_markdown_path(path: Path) -> Path | None:
    candidate = path.with_suffix(".md")
    if candidate.is_file():
        return candidate
    sibling = path.parent / "proposal.md"
    if sibling.is_file():
        return sibling
    return None


def collect_pending_proposals(proposal_root: str | Path) -> list[dict[str, Any]]:
    root = Path(proposal_root).expanduser().resolve()
    if not root.exists():
        raise GuardrailError(f"Proposal root does not exist: {root}")
    if not root.is_dir():
        raise GuardrailError(f"Proposal root is not a directory: {root}")

    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("proposal.json")):
        proposal = load_json(path)
        if not isinstance(proposal, dict):
            raise GuardrailError(f"Proposal must be a JSON object: {path}")
        status = _proposal_status(proposal)
        if status in {"applied", "rejected"}:
            continue
        targets = proposal.get("targets", [])
        evidence = proposal.get("evidence", [])
        report_path = _proposal_markdown_path(path)
        rows.append(
            {
                "proposal_id": _proposal_id(path, proposal),
                "source": str(proposal.get("source_id") or proposal.get("source") or "unknown"),
                "risk": str(proposal.get("risk_class") or proposal.get("risk") or "unknown"),
                "target_count": len(targets) if isinstance(targets, list) else 0,
                "evidence_count": len(evidence) if isinstance(evidence, list) else 0,
                "status": status,
                "proposal_path": str(path),
                "report_path": str(report_path) if report_path else None,
                "approval_required": bool(proposal.get("approval_required", True)),
                "dry_run_default": bool(proposal.get("dry_run_default", True)),
            }
        )
    return rows


def render_pending_markdown(rows: list[dict[str, Any]]) -> str:
    lines = ["# Pending Obsidian Operating Layer Proposals", ""]
    if not rows:
        lines.append("No pending proposals found.")
        return "\n".join(lines) + "\n"
    lines.append("| Proposal | Status | Risk | Targets | Evidence | Source | Report |")
    lines.append("| --- | --- | --- | ---: | ---: | --- | --- |")
    for row in rows:
        report = row["report_path"] or ""
        lines.append(
            "| "
            f"`{row['proposal_id']}` | `{row['status']}` | `{row['risk']}` | "
            f"{row['target_count']} | {row['evidence_count']} | `{row['source']}` | `{report}` |"
        )
    return "\n".join(lines) + "\n"


def explain_proposal(proposal_path: str | Path) -> dict[str, Any]:
    path = Path(proposal_path).expanduser().resolve()
    proposal = load_json(path)
    if not isinstance(proposal, dict):
        raise GuardrailError(f"Proposal must be a JSON object: {path}")
    if proposal.get("approval_required") is not True or proposal.get("dry_run_default") is not True:
        raise GuardrailError("Unsafe proposal explanation refused: proposal must require approval and default to dry-run")
    targets = proposal.get("targets", [])
    if not isinstance(targets, list):
        raise GuardrailError("Unsafe proposal explanation refused: targets must be a list")
    return {
        "proposal_id": _proposal_id(path, proposal),
        "status": _proposal_status(proposal),
        "risk": str(proposal.get("risk_class") or proposal.get("risk") or "unknown"),
        "summary": str(proposal.get("summary") or "No summary provided."),
        "what_will_change": [str(target.get("path", "<missing>")) for target in targets if isinstance(target, dict)],
        "target_count": len(targets),
        "approval_phrase": proposal.get("approval_phrase"),
        "next_safe_step": proposal.get("next_safe_step"),
        "rollback": proposal.get("backup_plan", {}),
        "proposal_path": str(path),
    }


def render_explanation_markdown(explanation: dict[str, Any]) -> str:
    paths = explanation["what_will_change"] or ["No targets listed"]
    lines = [
        f"# Proposal explanation: {explanation['proposal_id']}",
        "",
        f"- status: `{explanation['status']}`",
        f"- risk: `{explanation['risk']}`",
        f"- targets: `{explanation['target_count']}`",
        f"- approval phrase: `{explanation.get('approval_phrase')}`",
        "",
        "## Summary",
        "",
        explanation["summary"],
        "",
        "## What will change",
        "",
    ]
    lines.extend(f"- `{path}`" for path in paths)
    lines.extend(["", "## Next safe step", "", str(explanation.get("next_safe_step") or "Review before any apply.")])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Review Obsidian Operating Layer proposals without mutating any vault.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List pending proposals needing human review")
    list_parser.add_argument("--proposal-root", required=True, help="Directory containing proposal.json files")
    list_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of Markdown")
    list_parser.add_argument("--out", help="Optional output path for the rendered list")

    explain_parser = subparsers.add_parser("explain", help="Explain one safe dry-run proposal in human language")
    explain_parser.add_argument("--proposal", required=True, help="Path to proposal.json")
    explain_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of Markdown")
    explain_parser.add_argument("--out", help="Optional output path for the rendered explanation")

    args = parser.parse_args()
    if args.command == "list":
        rows = collect_pending_proposals(args.proposal_root)
        if args.json:
            payload = {"status": "ok", "count": len(rows), "proposals": rows}
            text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
            if args.out:
                write_json(args.out, payload)
            print(text, end="")
            return 0
        text = render_pending_markdown(rows)
        if args.out:
            Path(args.out).expanduser().resolve().write_text(text, encoding="utf-8")
        print(text, end="")
        return 0

    if args.command == "explain":
        explanation = explain_proposal(args.proposal)
        if args.json:
            payload = {"status": "ok", "explanation": explanation}
            text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
            if args.out:
                write_json(args.out, payload)
            print(text, end="")
            return 0
        text = render_explanation_markdown(explanation)
        if args.out:
            Path(args.out).expanduser().resolve().write_text(text, encoding="utf-8")
        print(text, end="")
        return 0

    raise GuardrailError(f"Unknown command: {args.command}")


def cli() -> int:
    try:
        return main()
    except (GuardrailError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
