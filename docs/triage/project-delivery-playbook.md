# Project delivery playbook — spec kit → GitHub → multi-agent triage Kanban

Updated: 2026-06-28T05:26:12Z

This document records what was done for Obsidian Operating Layer and the correct reusable process for future projects.

Required workflow markers: Spec kit, GitHub, multi-agent triage sandbox, Real Kanban board, gated slices, verification, push.

## What was done in this project

1. **Project normalized as a git repo**
   - Added packaging, `pyproject.toml`, `Makefile`, tests, lint/compile checks.
   - Canonical code placed under `src/obslayer/` and `tools/obsidian_*.py`.
   - Root wrappers kept thin.

2. **Safety-first Obsidian operating layer created**
   - `observe → propose → apply → verify` flow.
   - Dry-run by default.
   - Live writes require explicit approval manifest.
   - Protected paths enforced: `.obsidian`, `_Backups`, `_Archive`, `.trash`, Soul zones, secrets.

3. **Information gathered from ready components first**
   - Obsidian community plugin registry reviewed.
   - GitHub components searched via authenticated `gh`/GitHub API, not broad web search.
   - Ready MCP/RAG/graph/diagram candidates documented.
   - Custom code limited to glue/safety/enforcement.

4. **Spec kit created**
   - Full spec kit under `docs/spec-kit/`.
   - Includes component inventory, integration plan, final architecture, adapter contracts, queue schema, MCP sandbox plan, RAG/graph plan, diagram/PDF pipeline, roadmap.
   - JSON schemas added for adapter metadata and queue tasks.

5. **Reports written to Obsidian**
   - Human-readable reports saved under `/home/hermesadmin/Obsidian/Memory-Vault/Hermes/Reports/`.

6. **GitHub initialized and used as source of truth**
   - Private repo: `Lyti4/obsidian-operating-layer`.
   - Commits pushed after verified slices.

7. **Multi-agent triage sandbox connected**
   - Sandbox: `/home/hermesadmin/work/hermes-multi-agent-workflow-sandbox`.
   - Pipeline: `obsidian-infra-triage`.
   - Project brief and item records created.
   - Runtime artifacts kept out of git; stable control docs mirrored into project repo.

8. **Real Hermes Kanban board populated**
   - UI: `127.0.0.1:19119/kanban`.
   - Board: `Obsidian Infra Triage`.
   - 8 OOL tasks created as a sequential activation chain.
   - All assigned to `default` profile.
   - Each next slice activates only after the previous slice is complete.

9. **First implementation slices completed**
   - Sandbox harness and adapter sample records.
   - Read-only MCP adapter evaluation.
   - Tests, ruff, compile checks passed.
   - GitHub push completed.

## Current Kanban chain

1. `t_2bf7f62f` / `ool-phase03-readonly-mcp-adapter` — **done** — OOL: Phase 03 — read-only MCP adapter sandbox evaluation — assignee `default`
2. `t_141c87d4` / `ool-community-plugin-review` — **done** — OOL: Community plugin review — ready Obsidian components — assignee `default`
3. `t_9aae34b0` / `ool-github-components-refresh` — **done** — OOL: GitHub components refresh via gh API — assignee `default`
4. `t_10d14d0e` / `ool-phase04-rag-graph-adapter` — **running** — OOL: Phase 04 — RAG/graph adapter sandbox evaluation — assignee `default`
5. `t_9be6781d` / `ool-phase05-diagram-pdf-poc` — **todo** — OOL: Phase 05 — diagram/PDF proof of concept — assignee `default`
6. `t_71341c88` / `ool-phase06-proposal-normalization` — **todo** — OOL: Phase 06 — proposal normalization worker — assignee `default`
7. `t_43281d63` / `ool-phase07-obsidian-review-dashboard` — **todo** — OOL: Phase 07 — Obsidian review dashboard — assignee `default`
8. `t_5051d3ab` / `ool-phase08-controlled-autonomy` — **todo** — OOL: Phase 08 — controlled autonomy modules — assignee `default`

Current active card:

- `t_10d14d0e` — OOL: Phase 04 — RAG/graph adapter sandbox evaluation — `running` — assignee `default`

## Correct process for future projects

### 1. Intake and constraints

- Capture the user goal in one short project brief.
- Record hard constraints: safety, secrets, live-write policy, preferred components, forbidden areas.
- Identify whether this is a simple task or deep project work.

### 2. Create/normalize repo first

- Create or select a local repo.
- Add `AGENTS.md` with project-local rules.
- Add install/test/lint/run commands.
- Initialize git before large changes.
- Add `.gitignore` for caches, generated output, backups, local runtime.

### 3. Gather existing components before coding

- Search ready GitHub components with authenticated `gh`/GitHub API when GitHub research is needed.
- Inspect official/community registries for plugins or packages.
- Save raw/selected findings under `research/`.
- Prefer ready working pieces; write custom code only for glue, policy, safety, adapters, and verification.

### 4. Spec kit

Minimum spec kit:

- `00-overview.md`
- component inventory
- user goals / non-goals
- safety model
- integration plan
- final desired architecture
- adapter contracts
- local queue/task schema
- sandbox plan
- reporting/diagram/PDF plan
- implementation roadmap
- machine-readable schemas if workers will consume it

### 5. Put the project into multi-agent triage

- Use the existing sandbox when available.
- Add a project brief to the triage sandbox.
- Create one item per implementation slice.
- Keep each slice small, verifiable, and gated.
- Use subagents for research, audits, spec review, and candidate evaluation.

### 6. Populate the real Kanban board

- Use the Hermes Kanban board/API/DB, not only markdown notes.
- Create idempotent tasks with stable keys.
- Assign to the correct executor profile (`default` here).
- Encode sequential activation:
  - first completed/root slice = `done`;
  - current slice = `running` or `ready`;
  - future slices = `todo`;
  - next slice starts only after previous slice is `done`.
- Mirror the live board to repo docs for GitHub visibility.

### 7. Implement only through gated slices

For every slice:

1. Mark/claim Kanban triage item.
2. Produce or update triage run artifact.
3. Use subagent review if research/spec/audit is involved.
4. Implement the smallest useful code/docs change.
5. Run focused verification.
6. Add evidence to report/triage artifact.
7. Commit and push.
8. Mark slice done and activate the next card.

### 8. Verification rules

- Never claim success without tool output.
- For code: run tests/lint/compile or a focused equivalent.
- For config/DB/ignore behavior: create temporary `/tmp/hermes-verify-*` ad-hoc verification script, run it, delete it, and report as ad-hoc verification.
- For GitHub: verify commit/push output.
- For Obsidian live writes: require approval manifest, backup, post-verify.

### 9. Reporting rules

Every user update should include:

- result first;
- what was changed;
- where it lives;
- verification evidence;
- commit/push if applicable;
- current active Kanban slice.

## Git history evidence

- `b786b21` Initial safe Obsidian operating layer package
- `a06755f` Normalize project packaging and CLI hygiene
- `1965f9f` Add safe smoke runner
- `fb7ffb7` Add ready component research spec kit
- `000e0ac` Add diagram PDF reporting plan
- `34f0694` Add final desired architecture spec
- `e624075` Expand final architecture spec kit
- `fd4ebe4` Add spec kit schemas from subagent review
- `021675d` Add sandbox harness and adapter samples
- `978a3b2` Add read-only MCP adapter evaluation
- `cd3bf82` Add real triage kanban board mirror
- `4a57f57` Assign OOL triage chain to default profile

## Files to inspect

- `docs/spec-kit/`
- `docs/triage/kanban-board.md`
- `docs/triage/project-delivery-playbook.md`
- `/home/hermesadmin/work/hermes-multi-agent-workflow-sandbox/OBSIDIAN_OPERATING_LAYER_TRIAGE_BRIEF.md`
- `/home/hermesadmin/.hermes/kanban/boards/obsidian-infra-triage/kanban.db`
## Kanban state hygiene

For active multi-agent project work, keep exactly one lifecycle-state source of truth:

- **Kanban DB** holds card status, owner role, dependencies, comments, and events.
- **Markdown board mirrors** are generated/read-only views for GitHub and review; do not manually maintain a second backlog there.
- **Docs** hold policy, acceptance rules, and process contracts.
- **`out/` reports** hold evidence and worker/subagent outputs.
- Worker/subagent self-reports must be attached to card comments/events and verified by Hermes before a card advances.
- Roles belong in `assignee`/owner fields, not lifecycle columns; columns/statuses represent state (`todo`, `ready`, `running`, `blocked`, `done`, `cancelled`).

This prevents drift between DB status, markdown mirrors, report summaries, and final acceptance notes.
