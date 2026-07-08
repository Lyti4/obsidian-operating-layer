# Decisions — Obsidian Operating Layer

Durable project decisions only. Temporary task progress belongs in `HANDOFF.md`, Hermes Kanban, or reports.

## Accepted decisions

| Decision | Rationale | Source |
|---|---|---|
| Read-only-first operating model | Protect human memory/vault data. | `AGENTS.md`, `docs/spec-kit/03-safety-contract.md` |
| Proposal before apply | Human/Hermes acceptance must precede live mutation. | `AGENTS.md` |
| Single live mutation path | Easier to audit, backup, and verify. | `docs/ARCHITECTURE.md` |
| Hermes owns acceptance | Workers provide evidence, not authority. | `AGENTS.md` |
| Codex is bounded engineer/reviewer | Keeps implementation power inside scoped repo tasks. | `docs/agents/CODEX.md` |
| Nanobot is read-only/proposal worker | Keeps standing automation safe. | `docs/agents/NANOBOT.md` |
| Project skill budget is explicit | Prevents broad/noisy skill loading. | `docs/PROJECT_SKILLS.md` |

## Add a decision when

- it changes safety boundaries;
- it changes roles/ownership;
- it changes architecture or tool policy;
- it affects future sessions/delegation.
