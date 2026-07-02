# 20 — Indexing Runtime Acceptance

Status: accepted for sandbox and guarded read-only probes; not accepted for live mutation  
Date: 2026-06-29  
Scope: external indexing runtime wrapper, evidence, production-read-only boundary, and next integration blockers

## Purpose

This document closes the current state of `17-knowledge-indexing-update-plan.md` and `18-external-indexing-spike-plan.md` after the external indexing runtime work.

It records what is accepted, what remains blocked, and which evidence proves the current boundary.

## Decision summary

| Area | Decision |
|---|---|
| Knowledge indexing architecture | Accepted direction: derived catalog/index/cache, Obsidian remains source of truth |
| `DalecB/obsidian-semantic-mcp` candidate | Accepted as guarded sandbox/read-only backend candidate, not raw direct agent surface |
| Runtime wrapper | Accepted as mandatory boundary for candidate execution and transcript sanitization |
| Live vault access | Read-only probes may be evaluated only through guarded/dry-run paths; live writes remain out of scope |
| Semantic quality | Bounded real local `bge-m3` smoke accepted; full semantic quality/routine indexing still requires budgeted pass |
| Production integration | Not yet accepted; needs automatic MCP stdio wrapping, quality pass, and proposal normalization |

## Current accepted boundary

The accepted runtime boundary is:

```text
sandbox/live-read-only source
  ↓
external indexing candidate
  ↓
Obslayer indexing runtime wrapper
  ↓
validated tool surface + sanitized transcript + normalized provenance
  ↓
Hermes/Operating Layer proposal-only consumers
```

The wrapper is required because the raw candidate can return note snippets that contain absolute live-vault paths as note text. Those are not evidence of filesystem access, but they are still sensitive enough to require redaction before agent exposure.

## Evidence table

| Evidence | Path | Result |
|---|---|---|
| Contract/no-write sandbox scorecard | `out/reports/indexing-spike/indexing-spike-evaluation-DalecB-obsidian-semantic-mcp.md` | passed; sandbox tree unchanged; declared tools are read/index only |
| Real external sandbox run summary | `out/reports/external-indexing-spike/external-indexing-spike-summary.md` | partial pass; candidate ran under isolated Node 24, indexed sandbox, no live mutation; wrapper hardening required |
| Real local bge-m3 smoke | `out/reports/external-indexing-spike/real-bge-m3-semantic-smoke-2026-06-28.md` | bounded semantic smoke completed with local `bge-m3`; useful for capability evidence, not full routine-quality acceptance |
| Real local bge-m3 smoke safety | `out/reports/external-indexing-spike/external-indexing-spike-real-bge-m3-smoke-safety.json` | machine-readable safety evidence for the bounded smoke |
| External indexing final status | `out/reports/external-indexing-spike/external-indexing-spike-final-status-2026-06-28.md` | final run-state summary before later doc acceptance updates |
| Focused live read-only nested-excludes probe | `out/reports/external-indexing-spike/focused-live-readonly-nested-excludes-20260629T124944.md` | ok; live tree unchanged; dry-run indexed 462 and failed 0 |
| Live bge-m3 night run summary | `out/reports/external-indexing-spike/external-indexing-spike-live-bge-m3-night-summary.md` | live tree unchanged; tools allowlist ok; derived storage under MCP home; 154 indexed / 473 failed before nested exclude fix |
| Runtime wrapper source | `src/obslayer/indexing_wrapper.py` | enforces allowed tools, path policy, redaction, provenance normalization, and safe process spec construction |
| Runtime CLI harness | `tools/obsidian_indexing_runtime.py` | provides guarded runtime/transcript report path under `out/reports/external-indexing-spike` |
| Runtime auto-probe sample | `make indexing-runtime-auto-probe` | repeatable sandbox-only guardrail exercise; creates and sanitizes a sample transcript through the runtime boundary without live mutation |
| Runtime stdio fake harness | `make indexing-runtime-stdio-probe-fake` | repeatable subprocess stdio exercise against fake JSON-lines MCP server; writes raw/sanitized reports through the same runtime wrapper boundary without live mutation |
| Stdio protocol hardening | `tools/obsidian_indexing_stdio_probe.py` | validates `initialize` and `tools/list` before tool calls, drains stdout/stderr with bounded capture, fails closed on JSON-RPC errors, malformed JSON, timeout, and unapproved non-dry-run intent; timeout/close cleanup terminates the spawned process group; explicit sandbox-only derived-index writes require `--allow-derived-index-write` |
| Tests | `tests/test_indexing_wrapper.py`, `tests/test_indexing_runtime_cli.py`, `tests/test_indexing_stdio_probe.py` | cover unsafe paths, tool-surface failures, transcript sanitization, stdio subprocess probing, report-root refusal, runtime process spec guards, malformed JSON-RPC, failed initialize, tool mismatch, timeout, process-group child cleanup on timeout, secret/env leak refusal, sanitized diagnostics, default non-dry-run refusal, and explicit sandbox-derived non-dry-run allowance |

## What is accepted now

Accepted for the current project state:

1. Indexes and semantic databases are derived artifacts, not source of truth.
2. External indexing candidates must not be exposed raw to higher-level agents.
3. The runtime wrapper is the mandatory safety and normalization boundary.
4. Allowed candidate tools are exactly:
   - `index_status`
   - `index_vault`
   - `search_notes`
   - `read_note`
5. Extra, missing, malformed, duplicate, or write-like tools fail closed.
6. Sandbox candidate execution must stay under repo-local `out/sandbox-vaults/*` and `out/external-indexing-spike/*`.
7. Loopback-only embedding endpoints are allowed; remote/cloud embeddings remain blocked unless explicitly approved.
8. Absolute, traversal, drive-root, UNC-like, protected, or live-vault paths in candidate metadata fail closed or are redacted before transcript exposure.
9. The wrapper never passes the live vault as the candidate vault; the stdio harness also fingerprints the configured live vault before/after candidate execution and fails closed if it detects mutation. All note changes still require proposal/approval/apply/verify.
10. Bounded/overnight semantic indexing is acceptable only as an explicitly scoped resource-budgeted job on this VPS.
11. `make indexing-runtime-auto-probe` is accepted as the repeatable preflight for exercising the runtime wrapper boundary before wiring real MCP stdio calls.
12. `make indexing-runtime-stdio-probe-fake` is accepted as the deterministic CI/local harness for proving stdio subprocess wiring without npm/network dependencies.
13. The stdio harness fails closed on malformed JSON-RPC, failed or malformed `initialize`, extra/missing tool surface, timeouts, unsanitized diagnostics, secret parent-env inheritance, and unapproved non-dry-run intent.
14. Non-dry-run `index_vault` is accepted only for an explicit real-candidate sandbox gate: `--allow-derived-index-write`, a named repo-local sandbox vault under `out/sandbox-vaults/*`, derived storage under `out/external-indexing-spike/*`, sanitized reports under `out/reports/external-indexing-spike/*`, and no live-vault mutation.

## What is not accepted yet

Not accepted for production integration:

1. Direct raw candidate MCP connection from Codex/Hermes/agents.
2. Live write, patch, move, delete, rename, or Git operations through the indexing candidate.
3. Remote embeddings or paid/cloud model endpoints.
4. Full routine semantic quality claims based only on fake/stub Ollama, smoke runs, or incomplete night-run results.
5. Using indexed findings as automatic edits without Obslayer proposal normalization and approval manifest.
6. Treating the older night-run failure count as solved without the focused post-fix probe/evidence path.

## Status of docs 17 and 18

| Doc | Current interpretation |
|---|---|
| `17-knowledge-indexing-update-plan.md` | Architecture remains valid: FTS5/graph first, semantic sidecar second, read-only adapter behind safety boundary |
| `18-external-indexing-spike-plan.md` | Execution plan is mostly executed; stale pending wrapper/commit language is superseded by commits `aaa748e` and `15c457d` plus this acceptance file |
| `19-document-system-map.md` | Document map remains current, but its “next document” recommendation is now completed by this file |

## Known commits in this acceptance slice lineage

| Commit | Meaning |
|---|---|
| `aaa748e Add guarded indexing MCP runtime wrapper` | Adds guarded runtime wrapper/CLI functionality |
| `15c457d Harden indexing wrapper excludes` | Fixes fail-closed exclude validation and nested protected path handling |
| `580527e Systematize spec kit document map` | Adds the document system map and updated overview references |

## Remaining blockers before stronger integration

1. Run the real `@dalecb/obsidian-semantic-mcp` candidate through the stdio probe harness so every invocation automatically goes through the runtime wrapper.
2. Run a budgeted semantic quality pass with real local Ollama + `bge-m3` before treating semantic indexing as routine acceptance.
3. Add a stable Make target for the focused guarded live-read-only probe if it should become repeatable acceptance evidence.
4. Compare against `DeusData/codebase-memory-mcp` only as an isolated benchmark candidate, not as a replacement for the Obslayer safety boundary.
5. Normalize indexed findings into Obslayer proposal bundles with path, quote/span, hash/version, risk classification, and dry-run-only default.
6. Update Kanban/roadmap wording so Phase 04 reflects the indexing runtime acceptance state rather than the older generic RAG/graph phase label.

## Next implementation slice

Recommended next slice:

```text
indexing-runtime-real-candidate-stdio-probe
```

The stdio subprocess harness is now present and accepted against a fake JSON-lines MCP server; the remaining step is a guarded run against the real `@dalecb/obsidian-semantic-mcp` package.

Acceptance for that slice:

- real candidate stdio probe is launched only through the runtime wrapper, not through raw agent/Codex config;
- transcript reports are sanitized and written under `out/reports/external-indexing-spike`;
- tool surface is verified before accepting results;
- the configured live vault is fingerprinted before/after candidate execution and the probe fails closed on detected live-vault mutation;
- semantic mode is either verified with local `bge-m3` or explicitly marked blocked;
- any non-dry-run candidate indexing uses `--allow-derived-index-write` only against a named repo-local sandbox vault, with derived storage under `out/external-indexing-spike` and no live-vault mutation;
- `make verify` passes after code/doc changes.

## Stop conditions

Stop and ask before:

- live writes to `/home/hermesadmin/Obsidian`;
- destructive delete/move/merge;
- production deploy/restart/network exposure;
- paid/high-volume API/model pulls;
- secrets, browser profiles, `.env`, tokens;
- Soul governance/personality edits.
