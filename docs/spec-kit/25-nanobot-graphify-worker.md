# 25 — Nanobot Graphify Worker Contract

Status: active operating procedure  
Date: 2026-07-02  
Scope: Nanobot as the orchestrated Graphify worker for Obsidian semantic graph work

## Decision

Nanobot is the designated worker for Graphify-style semantic graph tasks, but not the acceptance owner and not a live-vault writer.

Hermes remains the control plane:

```text
Hermes prepares bounded task packet
  ↓
Nanobot runs Graphify through the Headroom URL bridge on gpt-5.4-mini
  ↓
Graph/report/proposal artifacts are written under out/
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
| route | Headroom URL bridge: `NANOBOT_OPENAI_CODEX_RESPONSES_URL=http://127.0.0.1:8787/v1/responses` |
| source | sandbox vault copy or approved read-only snapshot |
| outputs | graph JSON/Markdown, findings, proposal-only bundle |
| live writes | forbidden |
| embeddings | forbidden by default; separate approved stage only |

If the bridge is unavailable, the task must degrade to local structural analysis or stop. It must not silently switch to a heavier model or local embedding job.

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
NANOBOT_OPENAI_CODEX_RESPONSES_URL=http://127.0.0.1:8787/v1/responses
```

Expected path:

```text
Nanobot openai_codex provider
  ↓
Headroom URL proxy on 127.0.0.1:8787
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
