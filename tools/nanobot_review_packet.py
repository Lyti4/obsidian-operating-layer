#!/usr/bin/env python3
"""Build a compact Nanobot review packet from repo-only evidence.

The packet is meant for Nanobot read-only reviews: it combines gateway URLs
with a bounded git diff so Nanobot can review without broad filesystem access.
"""
from __future__ import annotations

import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_GATEWAY = "http://127.0.0.1:18791"
MAX_CHARS = 24000


def run_git(repo: Path, args: list[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return proc.stdout.strip()


def gateway_url(path: str, gateway: str) -> str | None:
    path = path.strip()
    if not path:
        return None
    suffix = Path(path).suffix.lower()
    safe_suffixes = {"", ".md", ".json", ".jsonl", ".txt", ".yaml", ".yml"}
    safe_names = {"AGENTS.md", "README.md", "Makefile"}
    if suffix not in safe_suffixes and Path(path).name not in safe_names:
        return None
    prefixes = {
        "docs/spec-kit/": "/spec-kit/",
        "docs/acceptance/": "/project-docs/acceptance/",
        "docs/": "/project-docs/",
        "out/reports/": "/reports/",
        "out/proposals/": "/proposals/",
        "AGENTS.md": "/project-policy/AGENTS.md",
        "README.md": "/project-policy/README.md",
        "Makefile": "/project-policy/Makefile",
    }
    for prefix, mapped in prefixes.items():
        if path == prefix.rstrip("/"):
            return gateway + mapped
        if path.startswith(prefix):
            return gateway + mapped + path[len(prefix):]
    return gateway + "/server-work/obsidian-operating-layer/" + path


def bounded(text: str, limit: int = MAX_CHARS) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    head = text[: limit // 2]
    tail = text[-limit // 2 :]
    marker = "\n\n...[TRUNCATED FOR NANOBOT PACKET]...\n\n"
    return head + marker + tail, True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="repo root")
    parser.add_argument("--slice", required=True, help="review slice id")
    parser.add_argument("--out", required=True, help="output markdown packet path")
    parser.add_argument("--gateway", default=DEFAULT_GATEWAY)
    parser.add_argument("--file", action="append", default=[], help="relevant repo path; repeatable")
    parser.add_argument("--note", action="append", default=[], help="extra scope/verification note; repeatable")
    ns = parser.parse_args()

    repo = Path(ns.repo).resolve()
    out = Path(ns.out)
    if not out.is_absolute():
        out = repo / out
    out.parent.mkdir(parents=True, exist_ok=True)

    status = run_git(repo, ["status", "--short"])
    names = ns.file or [line[3:].strip() for line in status.splitlines() if len(line) > 3]
    names = [name for name in dict.fromkeys(names) if name]
    diff_args = ["diff", "--", *names] if names else ["diff"]
    diff, truncated = bounded(run_git(repo, diff_args))
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        f"# Nanobot review packet — {ns.slice}",
        "",
        f"Generated UTC: {ts}",
        "",
        "## Contract",
        "",
        "- Mode: read-only review / proposal-only.",
        "- Acceptance owner: Hermes.",
        "- Allowed: read listed gateway URLs, analyze packet, return verdict.",
        "- Forbidden: live vault mutation, repo mutation, secret/auth/profile reads, "
        "service restart, cron creation, paid/high-volume actions.",
        "- Required verdict: `pass`, `concerns`, or `blocker` with short evidence.",
        "",
        "## Gateway roots",
        "",
        f"- Health: `{ns.gateway}/health`",
        f"- Snapshot: `{ns.gateway}/snapshot.json`",
        "",
        "## Relevant files and safe URLs",
        "",
    ]
    for name in names:
        url = gateway_url(name, ns.gateway)
        if url:
            lines.append(f"- `{name}` → `{url}`")
        else:
            lines.append(f"- `{name}` → diff-only in this packet; direct gateway read may be blocked by file-type policy")
    if not names:
        lines.append("- No explicit files supplied; review packet diff/status only.")
    lines += ["", "## Scope / verification notes", ""]
    for note in ns.note:
        lines.append(f"- {note}")
    if not ns.note:
        lines.append("- No extra notes supplied.")
    lines += ["", "## Git status", "", "```text", status or "clean", "```", "", "## Bounded diff", ""]
    if truncated:
        lines.append("> Diff was truncated for token safety; use safe URLs above for direct read-only follow-up.")
        lines.append("")
    lines += ["```diff", diff or "# no diff", "```", ""]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
