# Project Skill Cards — Obsidian Operating Layer

Purpose: short project-local skill cards. Use these as routing cards before loading full Hermes skills.

Source of truth: `docs/PROJECT_SKILLS.md` is the index. These files are the per-capability cards.

Every card inherits `AGENTS.md`, the applicable role contract, active feature
from `.specify/feature.json`, and the same-slice `documentation impact` duty.
A skill routes work; it never grants live or publication permission.

## Cards

- `obsidian-layer-triage-kanban.md` — project orchestration/Kanban workflow.
- `codex.md` — Codex implementation/review lane.
- `nanobot.md` — Nanobot read-only/proposal review lane.
- `obsidian.md` — Obsidian/vault operation lane.
- `graphify.md` — Graphify/indexing/embedding lane.

## Rule

Load the card matching the task. If it points to a full Hermes skill, load that skill only when the task needs it.

## If full Hermes skill is unavailable

Do not block on discovery. Use this card plus linked project docs as the task packet, record `skill_unavailable`, and continue only if the scope remains safe.
