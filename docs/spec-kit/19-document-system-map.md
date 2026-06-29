# 19 — Document System Map

Status: current project document index  
Date: 2026-06-29  
Scope: Obsidian Operating Layer documentation, plans, evidence, and next-layer orientation

## Purpose

This file systematizes the project documents so the current state is visible without re-reading the full spec kit.

Use it as the entry point when deciding what to run next.

## Current source-of-truth surfaces

| Surface | Path | Role |
|---|---|---|
| Project rules | `AGENTS.md` | Read-only-first operating rules and verification policy |
| Spec kit | `docs/spec-kit/` | Architecture, safety contract, plans, acceptance evidence |
| Kanban mirror | `docs/triage/kanban-board.md` | GitHub-visible mirror of the Hermes Kanban chain |
| Operator docs | `docs/operator-guide.md` | Human/operator usage guide |
| Generated evidence | `out/reports/` | Rebuildable run reports; not the canonical spec |
| Generated artifacts | `out/` | Sandbox vaults, derived indices, reports, diagrams |

## Reading order

For a fast orientation read:

1. `00-overview.md` — project purpose and top-level pipeline.
2. `05-final-desired-architecture.md` — desired layered architecture.
3. `19-document-system-map.md` — this current map.
4. `17-knowledge-indexing-update-plan.md` — current knowledge indexing direction.
5. `18-external-indexing-spike-plan.md` — external indexing runtime/spike plan.
6. `20-indexing-runtime-acceptance.md` — current accepted boundary for guarded indexing runtime work.
7. `14-operational-acceptance-report.md`, `15-manual-and-adapter-acceptance.md`, `16-sandbox-e2e-evidence.md` — accepted evidence.
8. `docs/triage/kanban-board.md` — active board chain.

## Spec kit document groups

### A. Foundation and architecture

| Doc | Status | Purpose |
|---|---|---|
| `00-overview.md` | active | Entry point and list of spec-kit files |
| `01-component-inventory.md` | baseline | Ready component inventory; mirrored by `docs/component-inventory.md` |
| `02-worker-orchestration.md` | baseline | Worker/queue/capability model |
| `03-safety-contract.md` | active invariant | Non-negotiable safety and adapter contract |
| `04-integration-plan.md` | superseded by later roadmaps but still useful | Original phased integration plan |
| `05-final-desired-architecture.md` | active | Final layered design and component choices |

### B. Contracts and execution schemas

| Doc | Status | Purpose |
|---|---|---|
| `06-adapter-contracts.md` | active | Adapter metadata, behavior, output normalization, acceptance checklist |
| `07-local-queue-schema.md` | active | Local durable task schema and worker execution rules |
| `08-mcp-sandbox-plan.md` | active for MCP benchmark design | Sandbox plan for MCP candidates |
| `09-rag-graph-sandbox-plan.md` | active for graph/RAG benchmark design | RAG/graph expected outputs and acceptance |
| `10-diagram-pdf-pipeline.md` | active | Diagram/PDF generation contract |

### C. Roadmaps and acceptance passes

| Doc | Status | Purpose |
|---|---|---|
| `11-implementation-roadmap.md` | baseline roadmap | Phase 0–8 sequence |
| `12-full-functional-and-diagram-test-plan.md` | executed test plan | Functional/diagram verification plan and snapshot |
| `13-next-improvements-roadmap.md` | mostly implemented baseline/P0/P1/P2/P3 map | Improvement backlog after MVP |
| `14-operational-acceptance-report.md` | accepted evidence | Operational acceptance summary |
| `15-manual-and-adapter-acceptance.md` | active acceptance addendum | Manual dashboard/diagram checks and adapter contracts |
| `16-sandbox-e2e-evidence.md` | accepted evidence | Safe sandbox/read-only E2E evidence |

### D. Knowledge indexing branch

| Doc | Status | Purpose |
|---|---|---|
| `17-knowledge-indexing-update-plan.md` | active | Defines the vault indexing upgrade: catalog + FTS5 + graph + optional semantic sidecar + read-only adapter |
| `18-external-indexing-spike-plan.md` | active, partly implemented | Defines real external-run spike for `DalecB/obsidian-semantic-mcp` and wrapper hardening/runtime path |
| `19-document-system-map.md` | active | Current documentation map and state-of-world |
| `20-indexing-runtime-acceptance.md` | active acceptance | Accepted guarded runtime boundary, evidence table, and remaining production-integration blockers |

### E. Research and run-specific notes

| Doc | Status | Purpose |
|---|---|---|
| `phase04-rag-graph-evaluation-2026-06-28.md` | evidence note | Phase 04 graph/RAG sandbox evaluation |
| `research/community-plugin-review-20260628.md` | research evidence | Community plugin shortlist and tiers |
| `research/github-components-refresh-2026-06-28.md` | research evidence | GitHub components refresh via API |
| `research/github-indexing-tools-refresh-20260628.md` | research evidence | Knowledge indexing candidate review |

## Non-spec docs

| Doc | Purpose |
|---|---|
| `docs/operator-guide.md` | How to operate the system safely |
| `docs/controlled-autonomy.md` | Controlled autonomy model and dry-run usage |
| `docs/telegram-summary-templates.md` | Short report templates for Telegram updates |
| `docs/report-template.md` | Generic project report template |
| `docs/component-inventory.md` | Top-level mirror of the component inventory |
| `docs/obsidian-review-dashboard/index.md` | Review dashboard source note |
| `docs/obsidian-review-dashboard/templates/report-template.md` | Acceptance report template |
| `docs/obsidian-review-dashboard/templates/review-note.md` | Review note template |
| `docs/triage/kanban-board.md` | Live Kanban mirror snapshot |
| `docs/triage/project-delivery-playbook.md` | Reusable project delivery process |

## Current architecture layers

The current system is organized as:

```text
Human/UI layer
  Obsidian, Dataview, Templater, Tasks, Linter, Omnisearch, dashboard, diagrams/PDF

Worker/MCP/index/RAG layer
  read/search/index/graph/report workers, external MCP candidates, derived caches only

Obslayer safety core
  observe → propose → verify → apply; dry-run by default; approval manifest required for live writes

Vaults and sandboxes
  live Obsidian vaults are source of truth; sandbox copies and indexes are rebuildable artifacts
```

## Current state after indexing-wrapper hardening

Recently closed slice:

- Commit: `15c457d Harden indexing wrapper excludes`
- Remote: `main == origin/main`
- Verification before commit: `make verify` passed (`pytest`, `ruff`, `compileall`).

What this closed:

- nested protected-path exclude discovery for indexing candidates;
- fail-closed validation of `OBSIDIAN_SEMANTIC_EXCLUDE` values;
- revalidation of direct `IndexingWrapperPolicy` construction;
- runtime-wrapper safety tests for unsafe exclude paths.

Relevant evidence:

| Evidence | Path |
|---|---|
| sandbox indexing scorecard | `out/reports/indexing-spike/indexing-spike-evaluation-DalecB-obsidian-semantic-mcp.md` |
| focused live read-only nested-excludes probe | `out/reports/external-indexing-spike/focused-live-readonly-nested-excludes-20260629T124944.md` |
| previous live night report | `out/reports/external-indexing-spike/external-indexing-spike-live-bge-m3-night-summary.md` |
| external indexing summary | `out/reports/external-indexing-spike/external-indexing-spike-summary.md` |

## What is current vs stale

| Item | Current interpretation |
|---|---|
| Phase 04 Kanban item | Historical board chain still says Phase 04 is active, but additional indexing documents 17/18 advanced beyond the original simple phase view |
| `18-external-indexing-spike-plan.md` line about commit/push pending | Resolved by commits `aaa748e` and `15c457d`; accepted state is now captured in `20-indexing-runtime-acceptance.md` |
| RAG/graph phase | Has sandbox evidence, but knowledge indexing branch became the more immediate active branch |
| Live mutation | Still not approved; live vault changes remain gated by proposal/apply manifest only |

## Latest completed document

The dedicated acceptance/state file has been created:

```text
20-indexing-runtime-acceptance.md
```

It records the status of `17` and `18`, evidence from sandbox/night/focused live-read-only probes, the accepted runtime boundary, and the remaining blockers before stronger production integration.

## Next implementation slice

Recommended next code/documentation slice after document `20`:

```text
indexing-runtime-auto-probe
```

Acceptance:

- route the real MCP stdio probe through the runtime wrapper automatically;
- keep transcript reports sanitized under `out/reports/external-indexing-spike`;
- optionally add a Make target for the focused guarded live-read-only indexing probe if it is stable enough;
- run `make verify`;
- keep generated reports under `out/` and committed docs/tests under `docs/` / `tests/`.

## Stop conditions

Stop and ask before:

- live writes to `/home/hermesadmin/Obsidian`;
- destructive delete/move/merge;
- production deploy/restart/network exposure;
- paid/high-volume API/model pulls;
- secrets, browser profiles, `.env`, tokens;
- Soul governance/personality edits.
