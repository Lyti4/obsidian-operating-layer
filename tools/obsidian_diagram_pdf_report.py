#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer import GuardrailError, build_diagram_pdf_report_evaluation

DEFAULT_ADAPTER_RECORD = "docs/spec-kit/research/sample-adapter-records/diagram-renderer-mermaid-cli.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render safe diagram SVG previews and a first PDF report under out/reports.")
    parser.add_argument("--adapter-record", default=DEFAULT_ADAPTER_RECORD, help="Diagram renderer metadata JSON record")
    parser.add_argument("--project-root", default=".", help="Project root containing docs/diagrams and out/")
    parser.add_argument("--diagram-out-dir", default="out/diagrams", help="Output directory for generated SVG diagrams")
    parser.add_argument("--report-out-dir", default="out/reports", help="Output directory for JSON/Markdown/PDF reports")
    args = parser.parse_args()

    project_root = Path(args.project_root).expanduser().resolve()
    adapter_record = Path(args.adapter_record)
    if not adapter_record.is_absolute():
        adapter_record = project_root / adapter_record
    generation_command = (
        "python tools/obsidian_diagram_pdf_report.py "
        f"--adapter-record {adapter_record} "
        f"--project-root {project_root} "
        f"--diagram-out-dir {args.diagram_out_dir} "
        f"--report-out-dir {args.report_out_dir}"
    )
    evaluation = build_diagram_pdf_report_evaluation(
        adapter_record=adapter_record,
        project_root=project_root,
        diagram_out_dir=args.diagram_out_dir,
        report_out_dir=args.report_out_dir,
        generation_command=generation_command,
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "adapter": evaluation.adapter,
                "json_report": evaluation.artifacts["json_report"],
                "markdown_report": evaluation.report_markdown,
                "pdf_report": evaluation.report_pdf,
                "diagram_outputs": evaluation.diagram_outputs,
                "pdf_generated": evaluation.verification["pdf_generated"],
                "direct_write_disabled": evaluation.direct_write_disabled,
                "no_live_vault_write": evaluation.verification["no_live_vault_write"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cli() -> int:
    try:
        return main()
    except GuardrailError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
