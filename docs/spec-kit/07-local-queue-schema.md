# Local Queue Schema

## Purpose

Start worker orchestration with a small local durable queue. Avoid heavy distributed infrastructure until the adapter model is proven.

## Storage layout

```text
out/queue/
  pending/
  running/
  done/
  failed/
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
  "status": "pending|running|done|failed|cancelled",
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
  }
}
```

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
pending -> running -> failed
pending -> cancelled
failed  -> pending  (manual retry)
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
