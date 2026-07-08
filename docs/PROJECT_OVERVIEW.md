# Project Overview — Obsidian Operating Layer

## End goal

A safe local operating layer for Obsidian: observe vault state, draft proposal-only changes, apply only approved changes with backup, and verify results.

## Current state

Production-like local project. Default mode is read-only/proposal-only. Live vault mutation requires explicit approval, backup, apply, and verify.

## Roles

| Role | Responsibility |
|---|---|
| Dmitry | Final human approval for risky/live actions. |
| Hermes | Orchestrator, safety boundary, acceptance owner. |
| Codex | Bounded implementation/review worker inside repo scope. |
| Nanobot | Supervised read-only/proposal/report worker. |
| External adapters | Read/search/analyze/render/propose only; no live apply ownership. |

## Architecture summary

```text
Obsidian vault
  ↑ verify/apply only through approved path
Obslayer safety core
  ↑ proposal bundles / reports
Workers/adapters: Hermes, Codex, Nanobot, Graphify, MCP, indexers
  ↑ read/search/analyze/render
Operator intent and acceptance
```

## Boundaries

- No live vault mutation without explicit approval manifest.
- No secrets in docs, prompts, logs, reports, or worker packets.
- No deploy/restart/cron/network exposure/account changes without explicit approval.
- External workers do not own final acceptance.

## Key docs

- `AGENTS.md` — authority, roles, safety rules.
- `docs/PROJECT_MAP.md` — repo orientation.
- `docs/ARCHITECTURE.md` — component/control-flow overview.
- `docs/TOOLS_POLICY.md` — allowed/forbidden tool use.
- `docs/PROJECT_SKILLS.md` — skill loading budget.
- `docs/DECISIONS.md` — durable project decisions.
- `docs/spec-kit/30-orchestrator-operating-spec.md` — detailed current orchestration spec.

## Acceptance

A change is accepted only when scope is clear, forbidden actions are avoided, relevant checks pass, and rollback/next step is documented.
