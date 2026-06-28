# Obsidian Operating Layer — real Hermes Kanban/Triage board

Updated: 2026-06-28T05:16:34Z

This is the GitHub-visible mirror of the real local Hermes Kanban board shown at `127.0.0.1:19119/kanban`.

- Board: `Obsidian Infra Triage`
- Board slug: `obsidian-infra-triage`
- Real DB: `/home/hermesadmin/.hermes/kanban/boards/obsidian-infra-triage/kanban.db`
- Project repo: `/home/hermesadmin/work/obsidian-operating-layer`
- Executor policy: all OOL spec-kit cards are assigned to the main `default` profile, not the weaker `dev` profile.
- Execution rule: every remaining spec-kit section is a gated slice; next slice activates only after its parent is `done`.

## Sequential activation chain

1. `t_2bf7f62f` / `ool-phase03-readonly-mcp-adapter` — **done** — OOL: Phase 03 — read-only MCP adapter sandbox evaluation — assignee `default` — parent `none/root`
2. `t_141c87d4` / `ool-community-plugin-review` — **ready** — OOL: Community plugin review — ready Obsidian components — assignee `default` — parent `t_2bf7f62f`
3. `t_9aae34b0` / `ool-github-components-refresh` — **todo** — OOL: GitHub components refresh via gh API — assignee `default` — parent `t_141c87d4`
4. `t_10d14d0e` / `ool-phase04-rag-graph-adapter` — **todo** — OOL: Phase 04 — RAG/graph adapter sandbox evaluation — assignee `default` — parent `t_9aae34b0`
5. `t_9be6781d` / `ool-phase05-diagram-pdf-poc` — **todo** — OOL: Phase 05 — diagram/PDF proof of concept — assignee `default` — parent `t_10d14d0e`
6. `t_71341c88` / `ool-phase06-proposal-normalization` — **todo** — OOL: Phase 06 — proposal normalization worker — assignee `default` — parent `t_9be6781d`
7. `t_43281d63` / `ool-phase07-obsidian-review-dashboard` — **todo** — OOL: Phase 07 — Obsidian review dashboard — assignee `default` — parent `t_71341c88`
8. `t_5051d3ab` / `ool-phase08-controlled-autonomy` — **todo** — OOL: Phase 08 — controlled autonomy modules — assignee `default` — parent `t_43281d63`

## Current active card

- `t_141c87d4` — OOL: Community plugin review — ready Obsidian components — assignee `default`

## Full chain semantics

```text
phase03(done, default)
  -> community-plugin-review(ready, default)
  -> github-components-refresh(todo, default)
  -> phase04-rag-graph-adapter(todo, default)
  -> phase05-diagram-pdf-poc(todo, default)
  -> phase06-proposal-normalization(todo, default)
  -> phase07-obsidian-review-dashboard(todo, default)
  -> phase08-controlled-autonomy(todo, default)
```

## Verification

Generated from the live Hermes Kanban SQLite DB and dependency table, not hand-written task IDs.
