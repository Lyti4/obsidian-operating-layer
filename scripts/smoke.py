#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> None:
    print("+ " + " ".join(cmd), flush=True)
    completed = subprocess.run(cmd, cwd=cwd, check=False, text=True)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Run a safe observe/propose/verify/apply dry-run smoke test.")
    parser.add_argument("--vault", default="/home/hermesadmin/Obsidian", help="Vault root to inspect read-only")
    parser.add_argument("--out-root", default=str(repo / "out"), help="Directory for generated smoke artifacts")
    args = parser.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(args.out_root).expanduser().resolve() / f"smoke-{stamp}"
    proposal_dir = run_dir / "proposal"
    proposal_dir.mkdir(parents=True, exist_ok=False)

    observe_path = run_dir / "observe.json"
    proposal_path = proposal_dir / "proposal.json"
    apply_path = run_dir / "apply-dry-run.json"

    py = sys.executable
    run([py, "tools/obsidian_observe.py", "--vault", args.vault, "--out", str(observe_path)], repo)
    run([py, "tools/obsidian_propose.py", "--observe", str(observe_path), "--out-dir", str(proposal_dir)], repo)
    run([py, "tools/obsidian_verify.py", "--observe", str(observe_path), "--proposal", str(proposal_path)], repo)
    run([py, "tools/obsidian_apply.py", "--proposal", str(proposal_path), "--out", str(apply_path)], repo)

    apply_payload = json.loads(apply_path.read_text(encoding="utf-8"))
    summary = {
        "status": "ok",
        "run_dir": str(run_dir),
        "vault_root": apply_payload.get("vault_root"),
        "apply_status": apply_payload.get("status"),
        "applied": apply_payload.get("applied", []),
        "approval_required": apply_payload.get("approval_required"),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    if summary["apply_status"] != "dry-run" or summary["applied"] != []:
        raise SystemExit("smoke expected dry-run with no applied changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
