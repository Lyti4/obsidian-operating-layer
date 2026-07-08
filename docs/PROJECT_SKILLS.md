# Project Skills — Obsidian Operating Layer

Purpose: skill router for this project. Use this file first, then the matching short card in `docs/skills/`, then the full Hermes skill only if needed.

## Source of truth

- Index: `docs/PROJECT_SKILLS.md`.
- Project skill cards: `docs/skills/*.md`.
- Agent contracts: `docs/agents/*.md`.
- Permissions and forbidden actions: `docs/TOOLS_POLICY.md`.

Do not duplicate full runbooks here. This file routes; detailed behavior lives in the linked card/spec/runbook.

## Start sequence

1. Read `AGENTS.md`.
2. Read the smallest relevant project entrypoint:
   - `docs/PROJECT_OVERVIEW.md`
   - `docs/PROJECT_MAP.md`
   - `docs/agents/*.md`
3. Read one matching skill card under `docs/skills/`.
4. Load the full Hermes skill only when the card says it is needed.

## Skill cards

| Task | Project card | Full Hermes skill |
|---|---|---|
| project orchestration / Kanban | `docs/skills/obsidian-layer-triage-kanban.md` | `obsidian-layer-triage-kanban` |
| Codex implementation/review | `docs/skills/codex.md` | `codex`, sometimes `codex-delegation-monitoring` |
| Nanobot review/scout | `docs/skills/nanobot.md` | `nanobot` |
| Obsidian/vault docs or approval flow | `docs/skills/obsidian.md` | `obsidian` |
| Graphify/indexing/embeddings | `docs/skills/graphify.md` | `graphify` only when graph tooling is needed |

## Do not load by default

- `graphify` for normal doc/code edits.
- broad research/web scraping skills.
- design/creative/media skills.
- heavy multi-agent skills unless the board/scope requires them.

## Acceptance rule

A skill tells Hermes how to work; it does not accept results. Hermes acceptance still requires scoped evidence, forbidden-action check, and real verification output.

## Skill unavailable fallback

If a full Hermes skill named by a card is unavailable, use the project card plus linked docs as the bounded task packet, record `skill_unavailable`, and continue only when the task remains inside safe repo/proposal scope.
