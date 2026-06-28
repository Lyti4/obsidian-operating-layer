# AGENTS.md — Obsidian Operating Layer

## Purpose

This workspace builds local tools and docs for a safe Obsidian operating layer. Treat the Obsidian vault as human memory and the toolchain as a read-only-first control plane.

## Ground rules

- Read before writing.
- Observe first; propose second; apply only with explicit approval.
- Apply defaults to dry-run.
- Any live change must be narrowly scoped, backed up, and verified.
- Do not touch secrets, money, public posting, production restarts, or network exposure.

## Working conventions

- Use absolute paths in logs and reports.
- Keep generated artifacts under `out/` unless the task says otherwise.
- Keep local generated/cache/backup artifacts out of git via `.gitignore`.
- Root-level `obsidian_*.py` files are wrappers only; canonical implementation lives in `tools/` and shared policy lives in `src/obslayer/`.
- Prefer JSON for machine-readable bundles and Markdown for human reports.
- Keep reports concise and include exact commands, changed files, and verification results.

## Safe apply policy

`obsidian_apply.py` must refuse real edits unless an approval manifest is provided. The manifest must explicitly name the target vault, the proposal file, and the approved change set.

## Verification policy

After any apply, run a fresh observation and compare it to the baseline. Stop on the first unexpected regression and report the mismatch clearly.
