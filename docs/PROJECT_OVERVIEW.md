# Project Overview — Obsidian Operating Layer

## End goal

A safe local operating layer for Obsidian: observe vault state, draft proposal-only changes, apply only approved changes with backup, and verify results.

## Operating model

Default mode is read-only/proposal-only. Current jobs, services and provider
state are intentionally not copied here; verify them in
`docs/RUNTIME_STATUS.md` before use.

## Roles

| Role | Responsibility |
|---|---|
| Dmitry | Final human approval for risky/live actions. |
| Hermes | Orchestrator, safety boundary, acceptance owner. |
| Codex | Bounded implementation/review worker inside repo scope. |
| Nanobot | Project-wide read-only/proposal observer. |
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
- `docs/INSTRUCTION_TREE.md` — precedence and document classification.
- `docs/PROJECT_MAP.md` — repo orientation.
- `docs/ARCHITECTURE.md` — component/control-flow overview.
- `docs/TOOLS_POLICY.md` — allowed/forbidden tool use.
- `docs/PROJECT_SKILLS.md` — skill loading budget.
- `docs/DECISIONS.md` — durable project decisions.
- `docs/tools/INDEX.md` — authoritative 58-tool registry.
- `.specify/feature.json` — active feature pointer under `specs/`.
- `docs/RUNTIME_STATUS.md` — current verify-before-use runtime source.

Numbered files under `docs/spec-kit/` are retained design/history sources. They
do not override the active feature or current runtime source.

## Acceptance

A change is accepted only when scope is clear, forbidden actions are avoided, relevant checks pass, and rollback/next step is documented.
