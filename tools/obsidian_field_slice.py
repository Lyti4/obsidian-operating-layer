#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _bootstrap import SRC  # noqa: F401

from obslayer import GuardrailError, write_json


def run_command(args: list[str]) -> dict[str, Any]:
    completed = subprocess.run(args, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise GuardrailError(f"command failed ({completed.returncode}): {' '.join(args)}\n{completed.stderr}{completed.stdout}")
    stdout = completed.stdout.strip()
    if stdout.startswith("{"):
        return json.loads(stdout)
    json_start = stdout.find("{")
    if json_start >= 0:
        return json.loads(stdout[json_start:])
    return {"stdout": completed.stdout}


def build_field_finding(vault_root: Path, observation: dict[str, Any]) -> dict[str, Any]:
    samples = observation.get("sample_notes") or []
    markdown_samples = [str(item) for item in samples if str(item).endswith((".md", ".markdown"))]
    if not markdown_samples:
        raise GuardrailError("field slice requires at least one markdown sample note")
    rel = markdown_samples[0]
    target = vault_root / rel
    text = target.read_text(encoding="utf-8")
    marker = "\n<!-- obslayer field-slice proposal only; not applied -->\n"
    return {
        "id": "field-slice-review-marker",
        "type": "field-slice-proposal-only",
        "severity": "low",
        "risk": "low",
        "evidence": f"Selected sample note from read-only observation: {rel}",
        "targets": [
            {
                "path": rel,
                "old_text": text,
                "new_text": text + marker if marker not in text else text,
            }
        ],
    }


def render_decision_markdown(decision: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Field Slice Decision Record",
            "",
            f"- task_id: `{decision['task_id']}`",
            f"- decision: `{decision['decision']}`",
            f"- vault_root: `{decision['vault_root']}`",
            f"- proposal: `{decision['proposal_path']}`",
            f"- verify: `{decision['verify_path']}`",
            f"- dashboard_list: `{decision['dashboard_list_path']}`",
            "- live_apply: `not-run`",
            "- mutation_boundary: proposal-only; no vault write performed",
            "",
            "## Reason",
            "",
            decision["reason"],
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a proposal-only field slice: observe -> finding -> proposal -> verify -> dashboard list -> decision record."
    )
    parser.add_argument("--vault", required=True, help="Approved vault or sandbox subset to inspect read-only")
    parser.add_argument("--out-root", required=True, help="Output directory, preferably under out/field-slices")
    parser.add_argument("--task-id", default="field-slice")
    parser.add_argument("--decision", choices=["pending", "rejected", "approved-for-review"], default="pending")
    parser.add_argument("--reason", default="Field slice acceptance record; no live apply was performed.")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    vault_root = Path(args.vault).expanduser().resolve()
    out_root = Path(args.out_root).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    observe_path = out_root / "observe.json"
    observe_summary = run_command(
        [sys.executable, str(repo / "tools" / "obsidian_observe.py"), "--vault", str(vault_root), "--out", str(observe_path)]
    )
    observation = json.loads(observe_path.read_text(encoding="utf-8"))

    findings_path = out_root / "findings.json"
    finding = build_field_finding(vault_root, observation)
    write_json(
        findings_path,
        {
            "source_id": args.task_id,
            "findings": [finding],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mutation_boundary": "proposal-only",
        },
    )

    proposal_dir = out_root / "proposals" / args.task_id
    proposal_summary = run_command(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_proposal_worker.py"),
            "--findings",
            str(findings_path),
            "--vault-root",
            str(vault_root),
            "--out-dir",
            str(proposal_dir),
        ]
    )
    proposal_path = Path(proposal_summary["proposal_json"])

    verify_path = out_root / "verify.json"
    verify_summary = run_command(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_verify.py"),
            "--observe",
            str(observe_path),
            "--proposal",
            str(proposal_path),
        ]
    )
    write_json(verify_path, verify_summary)

    dashboard_list_path = out_root / "pending-proposals.json"
    dashboard_summary = run_command(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_review_dashboard.py"),
            "list",
            "--proposal-root",
            str(out_root / "proposals"),
            "--json",
            "--out",
            str(dashboard_list_path),
        ]
    )

    decision = {
        "task_id": args.task_id,
        "decision": args.decision,
        "reason": args.reason,
        "vault_root": str(vault_root),
        "proposal_path": str(proposal_path),
        "verify_path": str(verify_path),
        "dashboard_list_path": str(dashboard_list_path),
        "live_apply": "not-run",
        "mutation_boundary": "proposal-only",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    decision_json = out_root / "decision.json"
    decision_md = out_root / "decision.md"
    write_json(decision_json, decision)
    decision_md.write_text(render_decision_markdown(decision), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "ok",
                "task_id": args.task_id,
                "observe": str(observe_path),
                "findings": str(findings_path),
                "proposal": str(proposal_path),
                "verify": str(verify_path),
                "dashboard_list": str(dashboard_list_path),
                "decision": str(decision_json),
                "live_apply": "not-run",
                "observe_summary": observe_summary,
                "verify_summary": verify_summary,
                "dashboard_summary": dashboard_summary,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cli() -> int:
    try:
        return main()
    except (GuardrailError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
