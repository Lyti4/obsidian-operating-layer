#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer.llm_channel_smoke import llm_channel_smoke_to_markdown, run_llm_channel_smoke


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a secret-free LLM channel smoke artifact.")
    parser.add_argument("--registry", default="docs/spec-kit/channel-registry.json")
    parser.add_argument("--out-dir", default="out/reports/llm-channel-smoke/manual")
    parser.add_argument("--live-probes", action="store_true", help="Probe local Headroom/evidence-gateway health endpoints.")
    args = parser.parse_args()

    report = run_llm_channel_smoke(args.registry, live_probes=args.live_probes)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "llm-channel-smoke.json").write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "REPORT.md").write_text(llm_channel_smoke_to_markdown(report), encoding="utf-8")
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    if report.status != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
