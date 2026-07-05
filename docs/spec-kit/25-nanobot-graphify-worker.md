# 25 — Nanobot Graphify Worker Contract

Status: active operating procedure  
Date: 2026-07-02  
Scope: Nanobot as the orchestrated Graphify worker for Obsidian semantic graph work


> Update 2026-07-04: global external LLM routing is governed by `28-global-headroom-only-llm-channel.md`. The accepted Graphify external path is `graphify-headroom` + `codex-cli` through Headroom. The accepted Nanobot review path is `/home/hermesadmin/.nanobot-hermes/bin/nanobot-headroom-agent`, which targets Headroom's Codex backend bridge at `http://127.0.0.1:8787/backend-api/codex/responses`. Do not use alternate HTTP bridge guesses for Nanobot.

## Decision

Nanobot is the designated worker for Graphify-style semantic graph tasks, but not the acceptance owner and not a live-vault writer.

Hermes remains the control plane:

```text
Graphify evidence/report selects the next bounded packet
  ↓
Hermes copies only the approved/sanitized packet into Nanobot workspace
  ↓
Nanobot reads the local packet and produces a report/proposal draft
  ↓
Hermes verifies safety, quality, load, and proposal shape
  ↓
Optional approval manifest path for any later live apply
```

## Why graph-first

Graph-first is safer than embedding-first for the current server and vault:

- lower CPU/RAM pressure than full embedding runs;
- useful structure appears before vector cost: links, backlinks, clusters, duplicates, orphans, weak edges;
- easier to decide what actually needs embeddings;
- avoids long-running local embedding jobs until there is a reviewed target set;
- keeps live vault untouched while the semantic layer is still being evaluated.

## Model and bridge policy

Default Graphify worker route:

| Field | Value |
|---|---|
| worker | Nanobot |
| model | `gpt-5.4-mini` |
| route | Headroom/Codex bridge; prefer Graphify `--backend codex-cli --model gpt-5.4-mini` for native Graphify semantic extraction, or `/home/hermesadmin/.nanobot-hermes/bin/nanobot-headroom-agent` with `NANOBOT_OPENAI_CODEX_RESPONSES_URL=http://127.0.0.1:8787/backend-api/codex/responses` for Nanobot worker calls |
| source | sandbox vault copy or approved read-only snapshot |
| outputs | graph JSON/Markdown, findings, proposal-only bundle |
| live writes | forbidden |
| embeddings | forbidden by default; separate approved stage only |

If the bridge is unavailable, the task must degrade to local structural analysis or stop. It must not silently switch to a heavier model or local embedding job.

Native Graphify semantic extraction should use the local Codex CLI backend when available:

```bash
graphify extract <sandbox-corpus>   --backend codex-cli   --model gpt-5.4-mini   --max-concurrency 1   --max-workers 1
```

This route inherits the approved Codex provider configuration (`provider=headroom`, localhost Headroom base URL) and avoids raw OpenAI-compatible API keys. Keep the first reruns bounded to tiny/small sandbox corpora, then run `graphify cluster-only`, inspect `GRAPH_REPORT.md`, and use `graphify query/path/explain --graph <graph.json>` before any proposal packet.

## Graphify-directed Nanobot loop

Graphify should drive Nanobot by evidence packets, not by giving Nanobot broad filesystem reach.

Required loop:

```text
Graphify report / graph.json / findings
  → bounded task packet
  → sanitized copy inside Nanobot's restricted workspace
  → Nanobot observe/report-only analysis
  → Hermes review and archival under out/reports/
```

When Nanobot runs with `restrictToWorkspace=true`, it must not be pointed at project paths outside its workspace. Hermes should copy only the approved reports/evidence into a workspace-local inbox packet such as `inbox/graphify-to-nanobot-.../`, ask Nanobot to write `REPORT.md` in that same packet directory, then copy the verified report back to this repository's `out/reports/`.

If Nanobot needs more context, it should request the missing skill, tool, or evidence in its report instead of expanding permissions, reading live vault paths, or changing configuration.

## Task packet shape

Nanobot Graphify tasks should be small and explicit:

```json
{
  "task_id": "graphify-YYYYMMDD-...",
  "worker": "nanobot-graphify",
  "model": "gpt-5.4-mini",
  "mode": "sandbox_read_only",
  "vault_snapshot": "out/sandbox-vaults/...",
  "allowed_capabilities": ["read", "search", "analyze", "graph", "propose"],
  "forbidden_capabilities": ["write", "delete", "move", "patch", "secret-read", "live-mutation", "embedding-auto-run"],
  "outputs": {
    "graph": "out/reports/graphify-.../graph.json",
    "report": "out/reports/graphify-.../report.md",
    "proposal": "out/reports/graphify-.../proposal.json"
  },
  "resource_limits": {
    "concurrency": 1,
    "batch_size": "small",
    "stop_on_high_load": true
  }
}
```

## Required workflow

1. Hermes creates or selects a sandbox vault snapshot.
2. Hermes excludes protected paths and secret-bearing paths before task dispatch.
3. Hermes emits a bounded Graphify task packet.
4. Nanobot runs Graphify with `gpt-5.4-mini` via the bridge.
5. Nanobot writes only derived artifacts under `out/`.
6. Hermes verifies:
   - no live vault file changed;
   - protected paths are absent from outputs;
   - secrets are not present in reports;
   - no embedding/indexing process was auto-started;
   - resource use stayed within the slice budget;
   - findings are evidence-backed and proposal-only.
7. Hermes promotes only reviewed findings into Obslayer proposal format.
8. Any live apply requires a separate approval manifest and the normal apply pipeline.

## Output expectations

Nanobot/Graphify should produce:

- note graph summary;
- topic clusters and candidate MOCs;
- orphan notes and weak-link candidates;
- duplicate/merge candidates;
- broken/nonexistent links;
- cleanup proposals with evidence;
- embedding candidate set, if useful, but not embeddings themselves.

## Official Graphify operating sequence

Graphify should be used as Graphify, not as a replacement name for generic RAG counting. RAG/adapter counts are useful only as a preflight/noise guardrail; they are not the main semantic deliverable. The canonical Graphify deliverables are `graphify-out/graph.json`, `graphify-out/GRAPH_REPORT.md`, optional `graph.html`, and optional exports/wiki/MCP artifacts.

For Obsidian Layer work, the safe sequence is:

1. Prepare a sandbox copy or narrow read-only snapshot of the vault. Never point Graphify at the live vault for exploratory work.
2. Add a `.graphifyignore` in the sandbox root before extraction. It should exclude protected/generated/noisy areas such as `.obsidian/`, `_Backups/`, `_Archive/`, `.trash/`, `out/`, derived reports, caches, secrets, browser profiles, and any Soul-protected paths not explicitly scoped.
3. Prefer the assistant skill path when Nanobot is the worker: dispatch a bounded task packet equivalent to `/graphify <sandbox-path> --no-viz` or `/graphify <sandbox-path> --wiki --no-viz` when an agent-crawlable wiki is needed.
4. For headless/scripted extraction, use `graphify extract <sandbox-path> --out <report-dir>` with an explicit backend/model. For Graphify Headroom runs, use the project-approved `graphify-headroom`/Codex CLI bridge after a healthy smoke check. Keep Nanobot on its canonical `nanobot-headroom-agent` backend Codex bridge. Do not print keys or token material.
5. Read `GRAPH_REPORT.md` first. Use the graph to answer project questions with `graphify query`, `graphify path`, and `graphify explain` before generating cleanup proposals.
6. Use `--update` only after the same sandbox corpus changes. Use `--cluster-only` only to relabel/recluster an existing graph. Do not treat either command as a full fresh semantic pass.
7. Use exports intentionally: `graphify export callflow-html` for readable architecture/call-flow pages, `--wiki` for markdown wiki, `--mcp`/`graphify.serve` for repeated tool access, and Neo4j/FalkorDB/GraphML/SVG only when the task packet asks for those artifacts.
8. If outputs exceed browser scale, skip HTML (`--no-viz`) and query `graph.json` directly.
9. Convert Graphify insights into Obslayer proposal-only findings only after Hermes review. Graphify/Nanobot never applies vault changes directly.

Minimum Graphify evidence for this project:

- exact sandbox/snapshot scope and `.graphifyignore` policy used;
- command or Nanobot task packet equivalent;
- model/backend route and Headroom health when semantic model work was used;
- `graphify-out/GRAPH_REPORT.md` and `graphify-out/graph.json` paths or copied report bundle;
- any `query`/`path`/`explain` prompts used for decisions;
- secret scan and protected-path target scan;
- confirmation that no live vault mutation and no embedding job occurred.

## Stop conditions

Stop immediately and report if:

- live vault files are touched;
- `.obsidian`, `_Backups`, `_Archive`, `.trash`, or Soul-protected paths appear as targets;
- any secret-like material appears in an output;
- the bridge attempts to use a non-approved model;
- a local embedding process starts unexpectedly;
- server load or memory pressure becomes unsafe;
- output cannot be traced back to source paths/hashes.

## Embedding handoff

Embeddings are a later, separate stage. A Graphify report may recommend embedding candidates, but actual embedding runs require a new slice with:

- sandbox/read-only source;
- explicit batch size;
- concurrency `1`;
- checkpoint/resume;
- `nice`/`ionice` when running local processes;
- load guard and abort threshold;
- no live mutation.

## Acceptance boundary

Accepted now:

- Nanobot as Graphify worker in sandbox/read-only mode;
- `gpt-5.4-mini` as default Graphify model through the bridge;
- graph/report/proposal artifacts under `out/`;
- Hermes review before any promotion.

Not accepted now:

- direct live-vault writes by Nanobot or Graphify;
- automatic embeddings;
- silent model escalation;
- direct apply without approval manifest;
- use of protected paths as targets.

## Headroom URL bridge

Nanobot/Graphify subscription inheritance uses the local Headroom URL bridge, not a direct upstream provider call.

Runtime setting:

```bash
NANOBOT_OPENAI_CODEX_RESPONSES_URL=http://127.0.0.1:8787/backend-api/codex/responses
```

Expected path:

```text
nanobot-headroom-agent / Nanobot openai_codex provider
  ↓
Headroom Codex backend bridge on 127.0.0.1:8787
  ↓
upstream API using the active Codex OAuth/subscription bearer
```

This setting is non-secret. OAuth tokens remain in the existing credential stores and must never be printed in reports. If the bridge is down, Nanobot must stop or degrade to local structural analysis; it must not silently bypass Headroom.

## Canonical safety references

Graphify tasks inherit the root protected-path and report-sanitization policy from `AGENTS.md` and shared tool policy. The canonical protected set includes `.obsidian`, `_Backups`, `_Archive`, `.trash`, Soul-protected paths, generated/cache paths, derived-index paths, and secret-bearing paths. A Graphify-specific checklist may add restrictions, but must not narrow the root policy.

## Bridge fallback rule

For semantic/model-backed Graphify work, the Headroom URL bridge must be healthy before making model claims. If the bridge or OAuth layer is unavailable, the task must either:

1. stop as `blocked` and return to Hermes; or
2. run only an explicitly labeled `local_structural_only` pass that makes no semantic/model claims, starts no embeddings, and produces a report that names the degraded mode.

No task may silently fall back to a direct provider or bypass the localhost Headroom URL bridge.

## Minimum evidence packet

Every Nanobot Graphify result must include:

- task packet ID and mode;
- source kind and sandbox/snapshot identifier;
- output artifact list;
- bridge/model route status when model work was used;
- protected-path target scan result;
- secret-scan result;
- mutation check result confirming no live-vault changes;
- confirmation that no cron, service restart, auth mutation, deploy, paid action, or embedding auto-run occurred;
- blocked/degraded conditions, if any.


## Graphify-derived embedding handoff

Embedding work must now consume a reviewed Graphify output first. The accepted handoff is:

```text
sandbox snapshot
  ↓
Graphify extract / cluster-only / query-path-explain
  ↓
graphify-out/graph.json + GRAPH_REPORT.md
  ↓
obslayer graphify embedding handoff manifest
  ↓
optional bounded embedding runner consumes only manifest candidates
```

Use `tools/obsidian_graphify_embedding_handoff.py` to create `embedding-manifest.json` and `REPORT.md` from `graphify-out/graph.json`. The handoff selects only eligible sandbox markdown/text source files referenced by Graphify nodes, scores them by graph participation, records hashes, and marks `embedding_policy.auto_execute=false`. It does not start embeddings. A later embedding runner must use that manifest as its allowlist, keep concurrency `1`, checkpoint/resume, write only derived cache under `out/external-indexing-spike/graphify-derived/`, and stop before live vault mutation.


## Bounded embedding runner

After the handoff manifest exists, the only approved embedding entrypoint is:

```bash
python3 tools/obsidian_graphify_embedding_run.py \
  --manifest out/reports/graphify-embedding-handoff/.../embedding-manifest.json \
  --out-dir out/reports/graphify-embedding-runs/... \
  --derived-root out/external-indexing-spike/graphify-derived/...
```

The runner is manifest-only: it refuses arbitrary file discovery, verifies sandbox file hashes against the Graphify-derived manifest, writes checkpoint/resume state, and stores vectors only in the derived cache. The primary semantic provider is local loopback Ollama with `bge-m3`; `local-hashing-v1` is allowed only with an explicit smoke/test gate and must be reported as non-semantic quality. The same manifest-only contract, concurrency `1`, checkpointing, and no live vault mutation apply to every provider. See `27-graphify-nanobot-embedding-orchestration.md` for the full role split and acceptance gates.

## Final468 sandbox embedding acceptance — 2026-07-04

The current Graphify-derived sandbox handoff has a completed full embedding/query acceptance pass:

- records: `468 / 468`
- processed: `467`
- skipped: `1` empty file (`empty_text_after_truncation`)
- embedding sidecar files: `467`
- query-smoke chunks: `3605`
- all JSON files in derived cache: `468`
- acceptance report: `out/reports/graphify-final468-acceptance-20260704T065729Z/REPORT.md`
- reusable query CLI: `tools/obsidian_graphify_embedding_query.py`

Operational rule learned on the 4 GB VPS: use safe batches with automatic Ollama unload and zram cleanup; do not use hot-mode for long series unless RAM is upgraded or thresholds are revalidated.

## Server-safe read-only evidence gateway rule

Repeated Nanobot handoffs should use the local server-safe read-only evidence gateway instead of copying the same project packets into Nanobot's workspace. The gateway is served only on loopback:

```text
http://127.0.0.1:18791/
```

Allowed roots:

Project evidence:

- `/reports/` -> project `out/reports/`
- `/proposals/` -> project `out/proposals/`
- `/queue/` -> project `out/queue/`
- `/spec-kit/` -> project `docs/spec-kit/`

Server-safe context:

- `/server-work/` -> `/home/hermesadmin/work/`
- `/server-user-systemd/` -> `/home/hermesadmin/.config/systemd/user/`
- `/server-local-bin/` -> `/home/hermesadmin/.local/bin/`
- `/hermes-skills/` -> `/home/hermesadmin/.hermes/skills/`
- `/hermes-cron/` -> `/home/hermesadmin/.hermes/cron/`
- `/nanobot-workspace/` -> `/home/hermesadmin/.nanobot-hermes/workspace/`
- `/nanobot-docs/` -> `/home/hermesadmin/.nanobot-hermes/docs/`

Safety contract:

- read-only HTTP only: `GET`, `HEAD`, `OPTIONS`; mutating methods return `405`;
- no raw `/`, live vault root, `~/secure`, `.ssh`, `.codex`, browser profile, or credential directory is exposed;
- hidden paths, traversal, symlink escapes, secret-like filenames, sensitive path names, unsafe extensions, and files over 2 MB are blocked;
- Nanobot's internal URL allowlist is prefix-scoped to this gateway URL, not CIDR-wide localhost access;
- Hermes remains acceptance owner and still writes `HERMES_VERIFICATION.md` for Nanobot claims.

Workspace-local copied packets remain a fallback for one-off sanitized bundles or when the gateway is intentionally stopped. Do not grant Nanobot broad filesystem permissions to project paths.
