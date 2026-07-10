#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer import GuardrailError, canonical_run_commands, load_json


def render_report(proposal: dict) -> str:
    run_commands = canonical_run_commands().to_dict()
    lines = [
        "# Obsidian Operating Layer Implementation Report",
        "",
        f"- generated_at: {datetime.now(timezone.utc).isoformat()}",
        f"- vault_root: `{proposal.get('vault_root', '')}`",
        f"- dry_run_default: `{proposal.get('dry_run_default', True)}`",
        f"- approval_required: `{proposal.get('approval_required', True)}`",
        f"- backup_dir: `{proposal.get('backup_plan', {}).get('backup_dir', '')}`",
        "",
        "## Exact commands",
        "",
        f"- observe: `{run_commands['observe']}`",
        f"- propose: `{run_commands['propose']}`",
        f"- apply: `{run_commands['apply']}`",
        f"- verify: `{run_commands['verify']}`",
        f"- backfill report: `{run_commands['backfill_report']}`",
        "",
        "## Changed files",
        "",
        "- `AGENTS.md`",
        "- `README.md`",
        "- `config/roles.yaml`",
        "- `manifests/approval_manifest.example.json`",
        "- `src/obslayer/guardrails.py`",
        "- `tools/_bootstrap.py`",
        "- `tools/obsidian_observe.py`",
        "- `tools/obsidian_propose.py`",
        "- `tools/obsidian_apply.py`",
        "- `tools/obsidian_verify.py`",
        "- `tools/obsidian_backfill_report.py`",
        "- `tests/conftest.py`",
        "- `tests/test_guardrails.py`",
        "",
        "## Tests",
        "",
        "- `python -m pytest -q`",
        "",
        "## Next safe apply step",
        "",
        f"{proposal.get('next_safe_step', 'Prepare approval manifest and author exact targets before any live apply.')}",
        "",
    ]
    return "\n".join(lines)


def report_output_path(reports_dir: Path, requested: str | None) -> Path:
    out = (
        Path(requested).expanduser().resolve()
        if requested
        else reports_dir / "obslayer-implementation-report.md"
    )
    try:
        out.relative_to(reports_dir)
    except ValueError as exc:
        raise GuardrailError("Report output is outside --reports-dir") from exc
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Write an Obsidian report note from a proposal bundle.")
    parser.add_argument("--proposal", required=True, help="Proposal JSON path")
    parser.add_argument("--reports-dir", required=True, help="Obsidian reports directory")
    parser.add_argument("--out", help="Optional explicit markdown output path")
    args = parser.parse_args()

    proposal = load_json(Path(args.proposal).expanduser().resolve())
    report_md = render_report(proposal)
    reports_dir = Path(args.reports_dir).expanduser().resolve()
    out = report_output_path(reports_dir, args.out)
    reports_dir.mkdir(parents=True, exist_ok=True)
    try:
        with out.open("x", encoding="utf-8") as handle:
            handle.write(report_md)
    except FileExistsError as exc:
        raise GuardrailError(f"Report output already exists: {out}") from exc
    print(json.dumps({"status": "ok", "out": str(out)}, indent=2, sort_keys=True))
    return 0


def cli() -> int:
    try:
        return main()
    except GuardrailError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
