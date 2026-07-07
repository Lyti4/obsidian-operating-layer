# Obsidian Operating Layer — real Hermes Kanban/Triage board

Updated: 2026-07-07T06:09:27Z

This is the GitHub-visible mirror of the real local Hermes Kanban board shown at `127.0.0.1:19119/kanban`.

## Board binding

- Board name: `Obsidian Infra Triage`
- Board slug: `obsidian-infra-triage`
- Real DB: `/home/hermesadmin/.hermes/kanban/boards/obsidian-infra-triage/kanban.db`
- Project repo: `/home/hermesadmin/work/obsidian-operating-layer`
- Executor policy: all OOL spec-kit cards are assigned by role (`dev`, `codex`, `ops`, `docs`, `nanobot`, `boardagent`) with Hermes as acceptance owner.
- Safety rule: Kanban status does not grant live vault apply authority; live edits still require explicit approval/backup/verify unless a standing policy says otherwise.

## Current active multi-agent triage slice

Triggered by Dmitry: continue through Obsidian Kanban triage with multi-agent cards and tracking.

| Card | Status | Assignee | Stable key |
|---|---:|---|---|
| `t_895339da` — [obsidian-operating-layer] kanban-multiagent-tracking-hygiene research_or_spec | `running` | `ops` | `obsidian-layer.kanban-multiagent-tracking-hygiene.research_or_spec` |
| `t_dedcf14b` — [obsidian-operating-layer] remaining-link-operator-nextgate research_or_spec | `running` | `nanobot` | `obsidian-layer.remaining-link-operator-nextgate.research_or_spec` |
| `t_db369d57` — [obsidian-operating-layer] standing-link-prefix-operator-workflow research_or_spec | `running` | `dev` | `obsidian-layer.standing-link-prefix-operator-workflow.research_or_spec` |
| `t_63727abe` — [obsidian-operating-layer] kanban-multiagent-tracking-hygiene docs_update | `todo` | `docs` | `obsidian-layer.kanban-multiagent-tracking-hygiene.docs_update` |
| `t_bf9860ca` — [obsidian-operating-layer] kanban-multiagent-tracking-hygiene final_report | `todo` | `boardagent` | `obsidian-layer.kanban-multiagent-tracking-hygiene.final_report` |
| `t_fdbc1ebe` — [obsidian-operating-layer] remaining-link-operator-nextgate code_slice | `todo` | `codex` | `obsidian-layer.remaining-link-operator-nextgate.code_slice` |
| `t_5799cdb4` — [obsidian-operating-layer] remaining-link-operator-nextgate final_report | `todo` | `boardagent` | `obsidian-layer.remaining-link-operator-nextgate.final_report` |
| `t_537a2d63` — [obsidian-operating-layer] remaining-link-operator-nextgate operator_review | `todo` | `default` | `obsidian-layer.remaining-link-operator-nextgate.operator_review` |
| `t_892cf4a6` — [obsidian-operating-layer] standing-link-prefix-operator-workflow code_slice | `todo` | `codex` | `obsidian-layer.standing-link-prefix-operator-workflow.code_slice` |
| `t_9f5bc2c4` — [obsidian-operating-layer] standing-link-prefix-operator-workflow docs_update | `todo` | `docs` | `obsidian-layer.standing-link-prefix-operator-workflow.docs_update` |
| `t_d6d55abd` — [obsidian-operating-layer] standing-link-prefix-operator-workflow final_report | `todo` | `boardagent` | `obsidian-layer.standing-link-prefix-operator-workflow.final_report` |
| `t_bccbc84d` — [obsidian-operating-layer] standing-link-prefix-operator-workflow ops_verification | `todo` | `ops` | `obsidian-layer.standing-link-prefix-operator-workflow.ops_verification` |

### Active workstreams

1. `standing-link-prefix-operator-workflow` — turn the read-only baseline tool into a normal operator/evidence workflow; future code/docs stages remain gated.
2. `remaining-link-operator-nextgate` — review remaining-link discovery/suppression surfaces and define the next proposal-only operator gate; no apply authority.
3. `kanban-multiagent-tracking-hygiene` — keep DB as source of truth, repo mirror as discoverability layer, and comments/events as execution log.

## Board counts

- `archived`: `12`
- `done`: `120`
- `running`: `3`
- `todo`: `9`

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
