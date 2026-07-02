# AGENTS.md — Obsidian Operating Layer

## Purpose

This workspace builds a safe local operating layer for Obsidian. Treat the Obsidian vault as human memory and the toolchain as a read-only-first control plane.

## Authority and roles

- **Hermes** is the orchestrator and acceptance owner: it prepares tasks, checks evidence, enforces safety, and decides whether a proposal can move toward approval.
- **Codex/subagents** may implement non-trivial code changes when requested, but must stay inside this repository and the active task scope.
- **Nanobot** may act as the Graphify worker only through the documented sandbox/read-only procedure in `docs/spec-kit/25-nanobot-graphify-worker.md`.
- External components, MCP servers, RAG engines, Graphify, and indexers are adapters. They may read/search/analyze/graph/propose/render, but they do not own live apply.

## Ground rules

- Read before writing.
- Observe first; propose second; apply only with explicit approval.
- Apply defaults to dry-run.
- Any live change must be narrowly scoped, backed up, and verified.
- Do not print or store secrets, tokens, cookies, private keys, `.env` values, or credential file contents.
- Do not touch money, public posting, production restarts, network exposure, or account/OAuth changes unless the user explicitly asks.

## Vault safety contract

Live vault mutation is allowed only through:

```text
observe → propose → review → explicit approval → backup → apply → verify
```

`tools/obsidian_apply.py` must refuse real edits unless an approval manifest is provided. The manifest must explicitly name the target vault, proposal file, target files, expected hashes, backup root, and approved change set.

Protected paths are not writable by adapters or workers:

- `.obsidian`
- `_Backups`
- `_Archive`
- `.trash`
- Soul-protected paths
- generated/cache/secret-bearing paths

## Graphify / indexing policy

- Graph-first before embedding-first.
- Graphify semantic work runs on sandbox copies first, not the live vault.
- Nanobot Graphify tasks use the subscription bridge with `gpt-5.4-mini` unless a later task explicitly overrides it.
- Embeddings are optional and later-stage only: small batches, single worker, `nice`/`ionice` where applicable, checkpoint/resume, and stop-on-load guardrails.
- No Graphify, MCP, RAG, or embedding component may directly write/delete/move notes in the live vault.

## Working conventions

- Use absolute paths in logs and reports.
- Keep generated artifacts under `out/` unless the task says otherwise.
- Keep local generated/cache/backup artifacts out of git via `.gitignore`.
- Root-level `obsidian_*.py` files are wrappers only; canonical implementation lives in `tools/` and shared policy lives in `src/obslayer/`.
- Prefer JSON for machine-readable bundles and Markdown for human reports.
- Keep reports concise and include exact commands, changed files, and verification results.

## Verification policy

After any apply, run a fresh observation and compare it to the baseline. Stop on the first unexpected regression and report the mismatch clearly.

For docs-only changes, run at minimum:

```bash
git diff --check
```

When code, schemas, workflows, or runtime behavior changes, run the relevant project verification target, usually:

```bash
make verify
```
