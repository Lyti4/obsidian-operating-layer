# Project Map — Obsidian Operating Layer

## Start here

- `README.md` — CLI and project layout.
- `AGENTS.md` — agent rules and safety boundaries.
- `HANDOFF.md` — short pointer only; it never overrides canonical docs or runtime.
- `docs/PROJECT_OVERVIEW.md` — concise project anchor.
- `docs/PROJECT_SKILLS.md` — skill loading budget.
- `docs/INSTRUCTION_TREE.md` — instruction precedence and lifecycle map.
- `.specify/feature.json` — active feature pointer.

## Agent entrypoints

- `docs/agents/HERMES.md` — Hermes authority/acceptance contract.
- `docs/agents/CODEX.md` — Codex implementation/review contract.
- `docs/agents/NANOBOT.md` — Nanobot read-only/proposal contract.

## Project skill cards

- `docs/PROJECT_SKILLS.md` — skill router/index.
- `docs/skills/README.md` — project skill-card set.
- `docs/skills/obsidian-layer-triage-kanban.md` — project orchestration/Kanban.
- `docs/skills/codex.md` — Codex lane.
- `docs/skills/nanobot.md` — Nanobot lane.
- `docs/skills/obsidian.md` — Obsidian/vault lane.
- `docs/skills/graphify.md` — Graphify/indexing lane.

## Core code

- `tools/` — canonical CLI implementations and operator tools.
- `docs/tools/INDEX.md` — one authoritative row for every tracked `tools/*.py`.
- `docs/tools/families/` — shared operating contracts for eight tool families.
- root `obsidian_*.py` files — compatibility wrappers around `tools/`.
- `src/obslayer/` — package code where present.
- `tests/` — pytest coverage.

## Operations and safety docs

- `docs/RUNTIME_STATUS.md` — current runtime/job status; verify before relying.
- `docs/operator-guide.md` — operator usage.
- `docs/runbooks/` — repeatable runbooks.
- `docs/controlled-autonomy.md` — controlled-autonomy notes.
- `docs/report-template.md` — reporting template.
- `SECURITY.md` — security notes.

## Planning system

- `.specify/` — current project-local Spec Kit infrastructure.
- `specs/` — active feature specifications, plans, tasks and evidence.
- `docs/spec-kit/` — preserved numbered design/history sources; not the active
  feature pointer or runtime authority.

Useful historical design sources:

- `docs/spec-kit/00-overview.md` — spec-kit index.
- `docs/spec-kit/03-safety-contract.md` — safety contract.
- `docs/spec-kit/26-nanobot-standing-worker.md` — Nanobot worker contract.
- `docs/spec-kit/30-orchestrator-operating-spec.md` — orchestrator design source.
- `docs/spec-kit/32-codex-hermes-communication-channel.md` — Codex/Hermes channel.
- `docs/spec-kit/33-codex-native-runtime.md` — Codex runtime.

## Generated / evidence paths

- `out/` — reports, proposals, queues, generated artifacts.
- `artifacts/` — proposal artifacts.
- `.hermes/plans/` — Hermes local plans.

## Protected / careful paths

- live Obsidian vault roots are outside this repo and require explicit approval for mutation.
- `.hermes-backups/` contains backups; do not casually edit/delete.
- Do not read or print secrets/auth/env/cookie/private-key material.


## Pre-commit docs integrity

Use the checklist in `README.md` before committing documentation-structure changes.
