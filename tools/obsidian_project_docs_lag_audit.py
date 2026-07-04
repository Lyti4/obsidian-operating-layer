#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer.project_docs_lag_audit import project_docs_lag_audit_to_markdown, run_project_docs_lag_audit


def main() -> None:
    parser = argparse.ArgumentParser(description="Check whether key spec-kit/docs markers lag behind implemented repo workflow.")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--out-dir", default="out/reports/project-docs-lag-audit/manual")
    args = parser.parse_args()

    audit = run_project_docs_lag_audit(args.repo)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "docs-lag-audit.json").write_text(json.dumps(audit.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "REPORT.md").write_text(project_docs_lag_audit_to_markdown(audit), encoding="utf-8")
    print(json.dumps(audit.to_dict(), ensure_ascii=False, indent=2))
    if audit.status != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
