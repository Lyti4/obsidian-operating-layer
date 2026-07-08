# Obsidian Operating Layer — real Hermes Kanban/Triage board

Updated: 2026-07-07T12:30:46Z

This is the GitHub-visible mirror of the real local Hermes Kanban board shown at `127.0.0.1:19119/kanban`.

## Board binding

- Board name: `Obsidian Infra Triage`
- Board slug: `obsidian-infra-triage`
- Real DB: `/home/hermesadmin/.hermes/kanban/boards/obsidian-infra-triage/kanban.db`
- Project repo: `/home/hermesadmin/work/obsidian-operating-layer`
- Executor policy: all OOL spec-kit cards are assigned by role (`dev`, `codex`, `ops`, `docs`, `nanobot`, `boardagent`) with Hermes as acceptance owner.
- Safety rule: Kanban status does not grant live vault apply authority; live edits still require explicit approval/backup/verify unless a standing policy says otherwise.
- State rule: DB = lifecycle state, docs = policy/mirror, `out/` = evidence.

## Current active multi-agent triage slice

Triggered by Dmitry: continue through Obsidian Kanban triage with multi-agent cards and tracking. This continuation slice is closed; no live vault mutation was authorized or performed.

| Card | Status | Assignee | Stable key |
|---|---:|---|---|
| `t_8c94d537` — [obsidian-operating-layer] R13 docs reconciliation after standing baseline | `done` | `docs` | `obsidian-layer.r13-doc-reconciliation.docs_update` |
| `t_63727abe` — [obsidian-operating-layer] kanban-multiagent-tracking-hygiene docs_update | `done` | `docs` | `obsidian-layer.kanban-multiagent-tracking-hygiene.docs_update` |
| `t_bf9860ca` — [obsidian-operating-layer] kanban-multiagent-tracking-hygiene final_report | `done` | `boardagent` | `obsidian-layer.kanban-multiagent-tracking-hygiene.final_report` |
| `t_895339da` — [obsidian-operating-layer] kanban-multiagent-tracking-hygiene research_or_spec | `done` | `ops` | `obsidian-layer.kanban-multiagent-tracking-hygiene.research_or_spec` |
| `t_5799cdb4` — [obsidian-operating-layer] remaining-link-operator-nextgate final_report | `done` | `boardagent` | `obsidian-layer.remaining-link-operator-nextgate.final_report` |
| `t_537a2d63` — [obsidian-operating-layer] remaining-link-operator-nextgate operator_review | `done` | `default` | `obsidian-layer.remaining-link-operator-nextgate.operator_review` |
| `t_dedcf14b` — [obsidian-operating-layer] remaining-link-operator-nextgate research_or_spec | `done` | `nanobot` | `obsidian-layer.remaining-link-operator-nextgate.research_or_spec` |
| `t_d6d55abd` — [obsidian-operating-layer] standing-link-prefix-operator-workflow final_report | `done` | `boardagent` | `obsidian-layer.standing-link-prefix-operator-workflow.final_report` |
| `t_db369d57` — [obsidian-operating-layer] standing-link-prefix-operator-workflow research_or_spec | `done` | `dev` | `obsidian-layer.standing-link-prefix-operator-workflow.research_or_spec` |
| `t_fdbc1ebe` — [obsidian-operating-layer] remaining-link-operator-nextgate code_slice | `cancelled` | `codex` | `obsidian-layer.remaining-link-operator-nextgate.code_slice` |
| `t_892cf4a6` — [obsidian-operating-layer] standing-link-prefix-operator-workflow code_slice | `cancelled` | `codex` | `obsidian-layer.standing-link-prefix-operator-workflow.code_slice` |
| `t_9f5bc2c4` — [obsidian-operating-layer] standing-link-prefix-operator-workflow docs_update | `cancelled` | `docs` | `obsidian-layer.standing-link-prefix-operator-workflow.docs_update` |
| `t_bccbc84d` — [obsidian-operating-layer] standing-link-prefix-operator-workflow ops_verification | `cancelled` | `ops` | `obsidian-layer.standing-link-prefix-operator-workflow.ops_verification` |

### Closed workstreams

1. `standing-link-prefix-operator-workflow` — R13 docs reconciliation done; superseded extra code/ops stages cancelled.
2. `remaining-link-operator-nextgate` — operator review done; no apply/code slice; final report done.
3. `kanban-multiagent-tracking-hygiene` — playbook rule done; final report done.

### Active-next clarification

This continuation closed the standing-policy/baseline and R13 reconciliation work. Already accepted historical lanes, including `lane-schema-v1`, must not be re-opened as the next active slice. The next valid project work is a fresh selector/regeneration pass against current remaining broken/ambiguous link evidence, followed by suppression/operator review; any live apply remains behind a fresh explicit approval manifest.

### Closure protocol for old work

Before creating any new card/swarm, reconcile these sources in order:

1. **Kanban DB** is runtime state: every previous continuation card must be `done`, `cancelled`, or `archived`; nonclosed count must be `0` unless Dmitry explicitly asks to resume that card.
2. **`docs/acceptance/index.md`** is the accepted-layer ledger: anything listed there is historical/accepted and must not be reopened as a new active slice without a fresh regression.
3. **`docs/spec-kit/37-vault-automation-indexing-roadmap.md`** is the current closure/next-target ledger.
4. **`docs/spec-kit/36-current-evidence-index.md`** is the evidence pointer ledger: `out/` reports are evidence, not source truth.
5. **Nanobot reports** are advisory/read-only evidence. They must be distilled into docs or explicit board comments before the work is considered closed; Nanobot does not advance, accept, or authorize live mutation.

Current board snapshot after cleanup: `done=160`, `cancelled=4`, `archived=18`, `nonclosed=0`.

2026-07-07 follow-up: two stale blocked cards were closed from the live Kanban DB after verification/reconciliation:

- `t_5b13d2bf` — unified-control-plane evidence index dispatcher blocker closed as implemented+verified; evidence `out/reports/unified-control-plane-index/hermes-verify-20260707T122859Z/REPORT.md`, focused tests 36 passed, `git diff --check` passed.
- `t_4815a2d6` — Codex council strategy lane closed as superseded by bounded sandbox selector/scorer evidence; no resource-heavy retry.

Live DB nonclosed state after close: `blocked=0`, `ready=0`, `running=0`, `todo=0`, `scheduled=0`.

## Board counts

- `archived`: `18`
- `cancelled`: `4`
- `done`: `160`

## Historical sequential activation chain

Previous chain retained for provenance:

1. `t_2bf7f62f` / `ool-phase03-readonly-mcp-adapter` — **done** — OOL: Phase 03 — read-only MCP adapter sandbox evaluation — assignee `default`
2. `t_141c87d4` / `ool-community-plugin-review` — **done** — OOL: Community plugin review — ready Obsidian components — assignee `default`
3. `t_9aae34b0` / `ool-github-components-refresh` — **done** — OOL: GitHub components refresh via gh API — assignee `default`
4. `t_10d14d0e` / `ool-phase04-rag-graph-adapter` — **done/legacy mirror may show running** — OOL: Phase 04 — RAG/graph adapter sandbox evaluation — assignee `default`
5. `t_9be6781d` / `ool-phase05-diagram-pdf-poc` — historical next — assignee `default`
6. `t_71341c88` / `ool-phase06-proposal-normalization` — historical next — assignee `default`
7. `t_43281d63` / `ool-phase07-obsidian-review-dashboard` — historical next — assignee `default`
8. `t_5051d3ab` / `ool-phase08-controlled-autonomy` — historical next — assignee `default`

## Verification

This file is generated from the live Hermes Kanban SQLite board. It is a GitHub-visible mirror, not the source of truth.

## 2026-07-07 fresh selector v3 board note

Current nonclosed DB state remains empty (`blocked=0`, `ready=0`, `running=0`, `todo=0`, `scheduled=0`). Fresh selector v3 was run directly as repo-only evidence, not as a new live-apply card.

Evidence:

- `out/reports/remaining-link-fresh-selector-v3/20260707T123534Z/REPORT.md`
- `out/reports/remaining-link-fresh-selector-v3/20260707T123534Z/manual-review-selector/REPORT.md`
- `out/reports/remaining-link-fresh-selector-v3/20260707T123534Z/operator-review-packet/REPORT.md`

Next board-worthy slice: manual-selector-to-operator-review adapter/code slice, because operator review currently blocks on `dry_run_proposals must be a list` when fed the manual selector packet.

## 2026-07-07 adapter slice board note

The previously board-worthy manual-selector-to-operator-review adapter slice is complete repo-side. Fresh selector v3 now has operator packet evidence at `out/reports/remaining-link-fresh-selector-v3/20260707T123534Z/operator-review-packet-adapter-v1/REPORT.md` with `ready_for_human_review`, 25 items, and `findings: []`.

Board remains empty for nonclosed work unless a new human-review/approval-manifest slice is intentionally opened.

- 2026-07-07: `remaining-link-fresh-selector-v3` acceptance ledger added: 25/25 manual-review candidates accepted as evidence-only/no-live-apply normalized Obsidian no-ops. Apply manifest remains not created because there are no concrete replacement targets.
- 2026-07-07: `full-vault-index-v1` built a read-only Memory-Vault index: 318 notes, 26 folders, 945 wikilinks, 858 resolved, 87 unresolved, 121 orphan notes, 0 duplicate-content groups. Artifacts: `out/reports/full-vault-index-v1/20260707T131041Z/REPORT.md`. Safety: no live mutation, no approval manifest, apply authority none.
- 2026-07-07: `broken-links-review-packet-v1` classified 87 unresolved links from full-vault index. Classes: {'protected_cross_vault_manual': 9, 'generated_report_auto_keep': 78}. Safety: no live mutation, no approval manifest, apply authority none. Artifacts: `out/reports/broken-links-review-packet-v1/20260707T132131Z/REPORT.md`.
- 2026-07-07: `protected-links-decision-v1` accepted 9 protected/cross-vault unresolved links as no-apply evidence: 8 concrete targets exist, 1 wildcard report pattern; no retarget/create/manifest/apply. Artifact: `out/reports/broken-links-review-packet-v1/20260707T132131Z/protected-links-decision-v1/REPORT.md`.
- 2026-07-07: `accepted-noise-bucket-v1` added operator buckets (human buckets): 78 generated/report links are accepted/no-apply noise, 9 Soul/cross-vault links are manual/protected, 0 target-discovery/apply items. Artifact: `out/reports/accepted-noise-bucket-v1/20260707T133300Z/REPORT.md`.
## 2026-07-08 Graphify incremental index docs-lag note

Nanobot scout lag around `graphify_incremental_index` was distilled into source docs without opening a new board card or live-apply lane. Minimal closure only: acceptance/evidence/roadmap pointers were added for the repo-only dry-run-first wrapper. Nanobot's larger proposals remain preserved for later review, not rejected or deleted.
