# Decisions — Obsidian Operating Layer

Durable project decisions only. Temporary progress belongs in active
`specs/*/tasks.md`, operator queues or evidence reports. `HANDOFF.md` is only a
pointer to those sources.

## Accepted decisions

| Decision | Rationale | Source |
|---|---|---|
| Read-only-first operating model | Protect human memory/vault data. | `AGENTS.md`, `docs/spec-kit/03-safety-contract.md` |
| Proposal before apply | Human/Hermes acceptance must precede live mutation. | `AGENTS.md` |
| Single existing-note edit path | Content edits use approved apply; a separate non-overwriting report-creation runbook is explicit. | `docs/ARCHITECTURE.md`, `docs/tools/INDEX.md` |
| Hermes owns acceptance | Workers provide evidence, not authority. | `AGENTS.md` |
| Codex is bounded engineer/reviewer | Keeps implementation power inside scoped repo tasks. | `docs/agents/CODEX.md` |
| Nanobot is project-wide read-only/proposal observer | Covers seven project areas without applying findings or enabling schedules. | `docs/agents/NANOBOT.md` |
| Project skill budget is explicit | Prevents broad/noisy skill loading. | `docs/PROJECT_SKILLS.md` |
| Active features use project-local Spec Kit | New work resolves through `.specify/feature.json`; numbered `docs/spec-kit/` remains history/design evidence. | `.specify/memory/constitution.md`, `docs/INSTRUCTION_TREE.md` |

## Add a decision when

- it changes safety boundaries;
- it changes roles/ownership;
- it changes architecture or tool policy;
- it affects future sessions/delegation.
