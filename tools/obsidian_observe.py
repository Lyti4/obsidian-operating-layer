#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer import DEFAULT_EXCLUDED_DIRS, GuardrailError, canonical_run_commands


def scan_vault(vault_root: Path, sample_limit: int = 20) -> dict:
    if not vault_root.exists():
        raise GuardrailError(f"Vault root does not exist: {vault_root}")
    if not vault_root.is_dir():
        raise GuardrailError(f"Vault root is not a directory: {vault_root}")

    counts = Counter()
    samples: list[str] = []
    protected_hits: list[str] = []

    for path in vault_root.rglob("*"):
        rel = path.relative_to(vault_root)
        parts = rel.parts
        if any(part in DEFAULT_EXCLUDED_DIRS for part in parts):
            if path.is_dir():
                # rglob still descends, but we do not record or sample excluded content.
                continue
        if path.is_file():
            counts[path.suffix.lower() or "<no_ext>"] += 1
            if len(samples) < sample_limit and path.suffix.lower() in {".md", ".markdown", ".json", ".yaml", ".yml"}:
                samples.append(str(rel))
            rel_str = rel.as_posix()
            if rel_str.startswith((".obsidian", "_Backups", "_Archive", ".trash")):
                protected_hits.append(rel_str)

    return {
        "vault_root": str(vault_root),
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "excluded_dirs": list(DEFAULT_EXCLUDED_DIRS),
        "file_counts": dict(sorted(counts.items())),
        "sample_notes": samples,
        "protected_hits": protected_hits,
        "run_commands": canonical_run_commands().to_dict(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a read-only observation artifact for the Obsidian operating layer.")
    parser.add_argument("--vault", default="/home/hermesadmin/Obsidian", help="Vault root to scan read-only")
    parser.add_argument("--out", required=True, help="Where to write the JSON observation artifact")
    args = parser.parse_args()

    payload = scan_vault(Path(args.vault).expanduser().resolve())
    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {"status": "ok", "out": str(out), "file_counts": payload["file_counts"], "sample_notes": payload["sample_notes"]},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
