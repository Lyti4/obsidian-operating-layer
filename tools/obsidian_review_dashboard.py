#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
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


def _target_diff(target: dict[str, Any], *, max_chars: int = 4000) -> dict[str, str]:
    target_path = str(target.get("path", "<missing>"))
    old_text = str(target.get("old_text", ""))
    new_text = str(target.get("new_text", ""))
    diff = "".join(
        difflib.unified_diff(
            old_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile=f"a/{target_path}",
            tofile=f"b/{target_path}",
            n=3,
        )
    )
    if not diff:
        diff = "# no textual old_text/new_text diff available\n"
    if len(diff) > max_chars:
        diff = diff[:max_chars].rstrip() + "\n... [diff truncated]\n"
    return {"path": target_path, "diff": diff}


def _markdown_cell(value: Any) -> str:
    text = str(value)
    return text.replace("\n", " ").replace("|", "\\|")


def _semantic_candidates(proposal: dict[str, Any], *, limit: int = 10) -> list[dict[str, Any]]:
    candidates = proposal.get("candidates", [])
    if not isinstance(candidates, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in candidates[:limit]:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "path": str(item.get("path") or "<missing>"),
                "best_score": item.get("best_score"),
                "hit_count": item.get("hit_count"),
                "queries": [str(query) for query in item.get("queries", []) if isinstance(query, str)],
                "chunks": item.get("chunks", []),
            }
        )
    return rows


def _targeted_candidate_paths(proposal: dict[str, Any], *, limit: int = 25) -> list[str]:
    candidate_paths = proposal.get("candidate_paths", [])
    if not isinstance(candidate_paths, list):
        return []
    return [str(path) for path in candidate_paths[:limit] if isinstance(path, str)]


def _proposed_changes(proposal: dict[str, Any]) -> list[str]:
    proposed_changes = proposal.get("proposed_changes", [])
    if not isinstance(proposed_changes, list):
        return []
    return [str(change) for change in proposed_changes if isinstance(change, str)]


def _is_safe_proposal_only(proposal: dict[str, Any], targets: list[Any]) -> bool:
    safety = proposal.get("safety", {})
    safety_proposal_only = isinstance(safety, dict) and safety.get("proposal_only") is True
    return (
        not targets
        and proposal.get("live_mutation_authorized") is False
        and (safety_proposal_only or str(proposal.get("mode", "")).startswith("semantic-"))
    )


def _approval_phrase(proposal: dict[str, Any], targets: list[Any]) -> str:
    if (
        proposal.get("mode") == "semantic-query-proposal-only-report"
        or proposal.get("live_mutation_authorized") is False
        or not targets
    ):
        return "not applicable — proposal-only / no targets"
    return str(proposal.get("approval_phrase") or "<missing>")


def explain_proposal(proposal_path: str | Path) -> dict[str, Any]:
    path = Path(proposal_path).expanduser().resolve()
    proposal = load_json(path)
    if not isinstance(proposal, dict):
        raise GuardrailError(f"Proposal must be a JSON object: {path}")
    targets = proposal.get("targets", [])
    if not isinstance(targets, list):
        raise GuardrailError("Unsafe proposal explanation refused: targets must be a list")
    if not _is_safe_proposal_only(proposal, targets) and (
        proposal.get("approval_required") is not True or proposal.get("dry_run_default") is not True
    ):
        raise GuardrailError("Unsafe proposal explanation refused: proposal must require approval and default to dry-run")
    target_dicts = [target for target in targets if isinstance(target, dict)]
    mode = str(proposal.get("mode") or "")
    summary = proposal.get("summary")
    return {
        "proposal_id": _proposal_id(path, proposal),
        "mode": mode,
        "status": _proposal_status(proposal),
        "risk": str(proposal.get("risk_class") or proposal.get("risk") or "unknown"),
        "summary": summary if isinstance(summary, dict) else str(summary or "No summary provided."),
        "what_will_change": [str(target.get("path", "<missing>")) for target in target_dicts],
        "target_diffs": [_target_diff(target) for target in target_dicts],
        "target_count": len(targets),
        "approval_phrase": _approval_phrase(proposal, targets),
        "next_safe_step": proposal.get("next_safe_step"),
        "rollback": proposal.get("backup_plan", {}),
        "proposal_path": str(path),
        "query_intents": [str(query) for query in proposal.get("queries", []) if isinstance(query, str)],
        "semantic_candidate_count": len(proposal.get("candidates", [])) if isinstance(proposal.get("candidates"), list) else 0,
        "semantic_candidates": _semantic_candidates(proposal),
        "targeted_candidate_paths": _targeted_candidate_paths(proposal),
        "proposed_changes": _proposed_changes(proposal),
        "source_decision_packet": proposal.get("source_decision_packet"),
        "safety": proposal.get("safety", {}) if isinstance(proposal.get("safety"), dict) else {},
        "live_mutation_authorized": bool(proposal.get("live_mutation_authorized", bool(targets))),
    }


def _render_summary(summary: Any) -> list[str]:
    if isinstance(summary, dict):
        return [f"- {key}: `{value}`" for key, value in summary.items()]
    return [str(summary)]


def render_explanation_markdown(explanation: dict[str, Any]) -> str:
    paths = explanation["what_will_change"] or ["No targets listed"]
    lines = [
        f"# Proposal explanation: {explanation['proposal_id']}",
        "",
        f"- mode: `{explanation.get('mode') or 'standard-proposal'}`",
        f"- status: `{explanation['status']}`",
        f"- risk: `{explanation['risk']}`",
        f"- targets: `{explanation['target_count']}`",
        f"- approval phrase: `{explanation.get('approval_phrase')}`",
        f"- live mutation authorized: `{explanation.get('live_mutation_authorized')}`",
        "",
        "## Summary",
        "",
    ]
    lines.extend(_render_summary(explanation["summary"]))
    lines.extend(["", "## What will change", ""])
    lines.extend(f"- `{path}`" for path in paths)

    proposed_changes = explanation.get("proposed_changes") or []
    targeted_paths = explanation.get("targeted_candidate_paths") or []
    if proposed_changes or targeted_paths:
        lines.extend(["", "## Targeted proposal review", ""])
        source_packet = explanation.get("source_decision_packet")
        if source_packet:
            lines.append(f"Source decision packet: `{source_packet}`")
            lines.append("")
        if proposed_changes:
            lines.extend(["### Proposed review actions", ""])
            lines.extend(f"- {change}" for change in proposed_changes)
            lines.append("")
        if targeted_paths:
            lines.extend(["### Candidate source paths", ""])
            lines.extend(f"- `{_markdown_cell(path)}`" for path in targeted_paths)
            lines.append("")
        lines.append("These paths are evidence/candidate inputs only; they are not live edit targets.")

    if explanation.get("semantic_candidate_count"):
        lines.extend(
            [
                "",
                "## Semantic review candidates",
                "",
                f"Candidate paths: `{explanation['semantic_candidate_count']}`",
                "",
            ]
        )
        queries = explanation.get("query_intents") or []
        if queries:
            lines.extend(["### Query intents", ""])
            lines.extend(f"- {query}" for query in queries)
            lines.append("")
        lines.extend(
            [
                "### Top candidates",
                "",
                "| rank | best score | hits | chunks | path | query matches |",
                "|---:|---:|---:|---|---|---|",
            ]
        )
        for index, item in enumerate(explanation.get("semantic_candidates") or [], 1):
            queries_text = _markdown_cell("; ".join(item.get("queries") or []))
            chunks = item.get("chunks", [])
            chunks_text = ", ".join(_markdown_cell(chunk) for chunk in chunks[:5]) if isinstance(chunks, list) else _markdown_cell(chunks)
            if isinstance(chunks, list) and len(chunks) > 5:
                chunks_text += ", ..."
            lines.append(
                f"| {index} | `{_markdown_cell(item.get('best_score'))}` | `{_markdown_cell(item.get('hit_count'))}` | `{chunks_text}` | "
                f"`{_markdown_cell(item['path'])}` | {queries_text} |"
            )
        lines.extend(
            [
                "",
                "Semantic candidates are review inputs only. They are not edit targets and do not authorize apply.",
            ]
        )

    diffs = explanation.get("target_diffs") or []
    if diffs:
        lines.extend(["", "## Proposed diff", ""])
        for item in diffs:
            lines.extend([f"### `{item['path']}`", "", "```diff", item["diff"].rstrip(), "```", ""])

    safety = explanation.get("safety") or {}
    if safety:
        lines.extend(["", "## Safety boundary", ""])
        for key, value in safety.items():
            lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Next safe step", "", str(explanation.get("next_safe_step") or "Review before any apply.")])
    return "\n".join(lines) + "\n"


REQUIRED_DASHBOARD_STATUSES = {"proposed", "needs-review", "applied", "rejected"}
REQUIRED_DASHBOARD_SECTIONS = (
    "## Safety contract",
    "## Status labels",
    "## Review queue",
    "## Proposal index",
    "## Report index",
    "## Task index",
    "## Manual review checklist",
)
REQUIRED_DATAVIEW_MARKERS = (
    'FROM "Hermes/Review"',
    'FROM "Hermes/Review/Proposals"',
    'FROM "Hermes/Reports"',
)


def validate_dashboard_source(dashboard_path: str | Path) -> dict[str, Any]:
    path = Path(dashboard_path).expanduser().resolve()
    if not path.is_file():
        raise GuardrailError(f"Dashboard source does not exist: {path}")
    text = path.read_text(encoding="utf-8")
    findings: list[str] = []

    if "write_policy: proposal_only" not in text:
        findings.append("frontmatter must include write_policy: proposal_only")
    if "status: proposed" not in text:
        findings.append("frontmatter must keep status: proposed until explicitly published")
    if "/home/hermesadmin/Obsidian" in text and "approved obslayer proposal/apply run" not in text:
        findings.append("live vault path mention must stay inside explicit publish-gate wording")
    if "```dataview" not in text:
        findings.append("dashboard must include Dataview blocks")

    for section in REQUIRED_DASHBOARD_SECTIONS:
        if section not in text:
            findings.append(f"missing required section: {section}")
    for marker in REQUIRED_DATAVIEW_MARKERS:
        if marker not in text:
            findings.append(f"missing Dataview source marker: {marker}")
    for status in REQUIRED_DASHBOARD_STATUSES:
        if f"`{status}`" not in text:
            findings.append(f"missing constrained status label: {status}")

    checklist_count = sum(1 for line in text.splitlines() if line.startswith("- [ ] "))
    if checklist_count < 5:
        findings.append("manual checklist must contain at least 5 unchecked safety items")

    result = {
        "status": "ok" if not findings else "failed",
        "dashboard_path": str(path),
        "required_sections": list(REQUIRED_DASHBOARD_SECTIONS),
        "dataview_sources": list(REQUIRED_DATAVIEW_MARKERS),
        "status_labels": sorted(REQUIRED_DASHBOARD_STATUSES),
        "checklist_items": checklist_count,
        "findings": findings,
    }
    if findings:
        raise GuardrailError("Dashboard validation failed: " + "; ".join(findings))
    return result


def render_dashboard_validation_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Obsidian Review Dashboard Validation",
        "",
        f"Status: `{result['status']}`",
        f"Dashboard: `{result['dashboard_path']}`",
        f"Checklist items: `{result['checklist_items']}`",
        "",
        "## Required sections",
        "",
    ]
    lines.extend(f"- {item}" for item in result["required_sections"])
    lines.extend(["", "## Dataview sources", ""])
    lines.extend(f"- `{item}`" for item in result["dataview_sources"])
    lines.extend(["", "## Status labels", ""])
    lines.extend(f"- `{item}`" for item in result["status_labels"])
    lines.extend(["", "## Findings", ""])
    if result["findings"]:
        lines.extend(f"- {item}" for item in result["findings"])
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Review Obsidian Operating Layer proposals without mutating any vault.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List pending proposals needing human review")
    list_parser.add_argument("--proposal-root", required=True, help="Directory containing proposal.json files")
    list_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of Markdown")
    list_parser.add_argument("--out", help="Optional output path for the rendered list")

    explain_parser = subparsers.add_parser("explain", help="Explain one safe dry-run proposal in human language")
    explain_parser.add_argument("proposal_path", nargs="?", help="Path to proposal.json (positional shorthand)")
    explain_parser.add_argument("--proposal", help="Path to proposal.json")
    explain_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of Markdown")
    explain_parser.add_argument("--out", help="Optional output path for the rendered explanation")

    validate_parser = subparsers.add_parser("validate-source", help="Validate the Dataview dashboard source without vault mutation")
    validate_parser.add_argument("--dashboard", default="docs/obsidian-review-dashboard/index.md", help="Dashboard markdown source")
    validate_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of Markdown")
    validate_parser.add_argument("--out", help="Optional output path for the rendered validation report")

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
        proposal_arg = args.proposal or args.proposal_path
        if not proposal_arg:
            explain_parser.error("the following argument is required: proposal_path or --proposal")
        explanation = explain_proposal(proposal_arg)
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

    if args.command == "validate-source":
        result = validate_dashboard_source(args.dashboard)
        if args.json:
            text = json.dumps(result, indent=2, sort_keys=True) + "\n"
            if args.out:
                write_json(args.out, result)
            print(text, end="")
            return 0
        text = render_dashboard_validation_markdown(result)
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
