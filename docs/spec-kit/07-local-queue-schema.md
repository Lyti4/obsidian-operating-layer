# Local Queue Schema

## Purpose

Start worker orchestration with a small local durable queue. Avoid heavy distributed infrastructure until the adapter model is proven.

## Storage layout

```text
out/queue/
  pending/
  running/
  blocked/
  done/
  failed/
  cancelled/
out/reports/
out/proposals/
out/research/
out/diagrams/
```

Queue files are JSON. Moving a file between directories changes state.

## Task schema

```json
{
  "task_id": "obslayer-20260628-120000-linker-001",
  "created_at": "2026-06-28T12:00:00Z",
  "status": "pending|queued|running|blocked|done|succeeded|failed|cancelled",
  "worker": "linker-worker",
  "priority": 50,
  "vault_root": "/home/hermesadmin/Obsidian",
  "vault_mode": "sandbox-copy|read-only-live|approved-live-output",
  "capabilities": ["read", "search", "graph", "propose"],
  "write_policy": "proposal_only",
  "inputs": {
    "paths": [],
    "query": null,
    "component_adapter": null
  },
  "outputs": {
    "finding": "out/reports/task.finding.json",
    "proposal": "out/proposals/task.proposal.json",
    "report": "out/reports/task.report.md",
    "diagrams": []
  },
  "limits": {
    "timeout_seconds": 600,
    "max_files": 1000,
    "max_output_bytes": 5000000
  },
  "safety": {
    "protected_paths_excluded": true,
    "direct_write_enabled": false,
    "requires_manifest_for_apply": true
  },
  "attempts": 0,
  "max_attempts": 3,
  "depends_on": [],
  "labels": []
}
```

Machine-readable schema: `schemas/queue-task.schema.json`.

## Initial workers

| Worker | Inputs | Outputs | Writes |
|---|---|---|---|
| `plugin-scout` | GitHub API / Obsidian registry | component inventory | no live writes |
| `index-worker` | markdown vault copy/read-only | index stats/report | no live writes |
| `graph-worker` | links/frontmatter/index | graph findings/MOC candidates | proposal only |
| `retrieval-worker` | query/index/RAG engine | search results/evidence | no live writes |
| `linker-worker` | related notes | candidate links | proposal only |
| `dedupe-worker` | near duplicates | merge candidates | proposal only |
| `cleaner-worker` | lint/metadata findings | cleanup proposal | proposal only |
| `memory-consolidator` | note clusters | summary/map proposal | proposal only |
| `diagram-worker` | architecture/task data | diagram source/PDF | out/reports first |
| `proposal-worker` | findings | normalized proposal | no apply |
| `report-worker` | all outputs | markdown report | approved paths only |

## State transitions

```text
pending -> running -> done
queued  -> running -> succeeded
pending -> running -> failed
queued  -> blocked  (missing dependency or approval)
pending -> cancelled
failed  -> pending  (manual retry)
```

`done` and `succeeded` are synonyms during the draft phase; implementation should pick one canonical value before coding.

## Retry and deduplication

- Retry only transient failures.
- Stop at `max_attempts`.
- Fail fast on protected path access, direct write attempts, secrets exposure, invalid vault root, or malformed proposal target.
- Deduplicate tasks by `worker`, `vault_root`, normalized `inputs`, and `write_policy`.

## Audit record

Every state transition should append an audit entry:

```json
{
  "task_id": "obslayer-20260628-120000-graph",
  "from_status": "queued",
  "to_status": "running",
  "worker": "graph-worker",
  "timestamp": "2026-06-28T12:01:00Z",
  "note": "claimed by worker"
}
```

## Execution rules

- One task = one narrow purpose.
- Every task records adapter/worker/version where possible.
- Workers must refuse protected paths before producing write-like proposals.
- Any write-like action becomes `proposal.json`.
- `apply` is not a queue worker in early phases; it remains a manually approved command.

## Acceptance criteria

- Queue can run a read-only task against sandbox vault.
- Failed task keeps logs and does not partially mutate live vault.
- Proposal output passes obslayer validation.
- Reports identify what was applied vs only proposed.

## Nanobot standing task packets

Standing Nanobot tasks use the same queue layout when a task needs persistence. Recommended worker names:

- `nanobot-standing-worker` for observe/proposal/communication hub duties;
- `nanobot-graphify` for graph-first semantic work described in `25-nanobot-graphify-worker.md`.

Recommended modes:

- `observe`;
- `proposal`;
- `communication_hub`;
- `graphify`.

Required safety fields for these tasks:

```json
{
  "safety": {
    "protected_paths_excluded": true,
    "direct_write_enabled": false,
    "requires_manifest_for_apply": true,
    "forbid_secret_read": true,
    "forbid_service_restart": true,
    "forbid_cron_create_without_user_approval": true,
    "forbid_embedding_auto_run": true
  }
}
```

Nanobot queue outputs are advisory until Hermes accepts them.
