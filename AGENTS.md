# AGENTS.md — Obsidian Operating Layer

## Purpose

This workspace builds a safe local operating layer for Obsidian. Treat the Obsidian vault as human memory and the toolchain as a read-only-first control plane.

## Instruction precedence and documentation duty

Apply instructions in this order: external system/developer/user instructions,
this root `AGENTS.md`, the nearest nested `AGENTS.md`, the relevant role
contract, the tool family guide, and the operation runbook. A narrower file
**must not weaken** root safety, permission, data, secret, or approval rules.

- `docs/INSTRUCTION_TREE.md` — canonical precedence, scope, and document-status map.
- `docs/AGENTS.md` — documentation lifecycle and same-slice update rules.
- `docs/agents/AGENTS.md` — common Hermes/Codex/Nanobot contract structure.
- `docs/tools/INDEX.md` — authoritative registry for every `tools/*.py` file.
- `tools/AGENTS.md` — CLI/internal-module development contract.
- `src/obslayer/AGENTS.md` — safety-core and trust-boundary contract.
- `tests/AGENTS.md` — isolated evidence and no-live-vault test contract.
- `.specify/memory/constitution.md` — Spec Kit governance.
- `.specify/feature.json` — active feature pointer under `specs/`.
- `docs/RUNTIME_STATUS.md` — current verify-before-use runtime state.

Every code, tool, workflow, runtime, or instruction change must update affected
canonical/active documents in the same slice or report
`documentation impact: none` with a reason. Adding or changing a tool also
updates its registry row, family guide, and test.


## Canonical project docs

Use the accepted entrypoint structure; do not replace it with ad-hoc “similar docs elsewhere”.

- `docs/PROJECT_OVERVIEW.md` — goal, status, role summary, boundaries.
- `docs/PROJECT_MAP.md` — repo/doc/evidence map.
- `docs/ARCHITECTURE.md` — component/control-flow overview.
- `docs/DECISIONS.md` — durable decisions only.
- `docs/TOOLS_POLICY.md` — permission boundary.
- `docs/PROJECT_SKILLS.md` — skill router.
- `docs/RUNTIME_STATUS.md` — current verify-before-use runtime/job status.
- `docs/agents/HERMES.md` — Hermes contract.
- `docs/agents/CODEX.md` — Codex contract.
- `docs/agents/NANOBOT.md` — Nanobot contract.
- `docs/skills/` — short project-local skill cards.

## Authority and roles

- **Hermes** is the orchestrator and acceptance owner: it prepares tasks, checks evidence, enforces safety, and decides whether a proposal can move toward approval.
- **Codex/subagents** may implement non-trivial code changes when requested, but must stay inside this repository and the active task scope.
- **Nanobot** may act as a standing maintenance/communication worker through `docs/spec-kit/26-nanobot-standing-worker.md`, as the Graphify worker through `docs/spec-kit/25-nanobot-graphify-worker.md`, and as a bounded connection-scout/proposal worker under `docs/spec-kit/28-global-headroom-only-llm-channel.md`.
- External components, MCP servers, RAG engines, Graphify, and indexers are adapters. They may read/search/analyze/graph/propose/render, but they do not own live apply.

## Ground rules

- Read before writing.
- Observe first; propose second; apply only with explicit approval.
- Apply defaults to dry-run.
- Any live change must be narrowly scoped, backed up, and verified.
- Do not print or store secrets, tokens, cookies, private keys, `.env` values, or credential file contents.
- Do not touch money, public posting, production restarts, network exposure, or account/OAuth changes unless the user explicitly asks.
- Do not create a commit, push a branch, or open/update a pull request unless the user explicitly approves that publication action.

## Codex implementation/review worker policy

Codex is the primary coding/review executor for non-trivial implementation work, but remains bounded by Hermes orchestration:

- allowed: repo-scoped implementation/review tasks, patch proposals, tests, and concise reports;
- forbidden without explicit approval: live vault mutation, auth/profile mutation, service restart, deployment, cron creation, network exposure, paid actions, public posting, and secret printing/storage;
- task communication uses the local Codex ⇄ Hermes channel in `docs/spec-kit/32-codex-hermes-communication-channel.md`;
- Hermes remains acceptance owner and must verify Codex outputs before reporting success.

Codex task packets/reports use `~/.codex-hermes/comm/` and the role policy in `~/.codex-hermes/docs/ROLE_POLICY.json`.

Codex native invocation uses `/home/hermesadmin/.codex-hermes/bin/hermes-codex-run` from `docs/spec-kit/33-codex-native-runtime.md`. Task/report packets are schema-versioned as `codex_task.v1` and `codex_report.v1` (`schemas/codex_task.v1.json`, `schemas/codex_report.v1.json`). Review mode must leave no diff; implementation mode must report changed files and verification.

## Nanobot standing worker policy

Nanobot can be involved continuously in project maintenance and inter-agent communication, but only as a supervised worker:

Nanobot's job is to say what it observes and what it recommends: architecture risks, simplification opportunities, scale bottlenecks, docs lag, proposal candidates, and possible Codex task suggestions. It does not dispatch Codex, approve patches, mutate the repo/vault/auth/services, or bypass Hermes acceptance.

- allowed: observe, summarize, route task packets, draft reports, draft proposal-only artifacts, run sandbox/read-only Graphify tasks;
- forbidden without explicit approval: live vault mutation, direct apply, cron creation beyond the approved local Nanobot scout/reviewer loop, service restart, deployment, auth/profile changes, paid actions, third-party GitHub App installs, automatic embeddings;
- Hermes remains responsible for acceptance, user communication, approval manifests, and final decisions.

Standing Nanobot task packets and reports should stay under `out/queue/`, `out/reports/`, or `out/proposals/` unless a task explicitly says otherwise.

Current Nanobot runtime/scheduled-loop state is tracked in `docs/RUNTIME_STATUS.md`. Treat it as verify-before-use status, not canonical acceptance policy.

Current verified state (2026-07-10): the approved Nanobot scout/reviewer/deep-review definitions still exist, but jobs `212b7e8f3c21`, `d2a5fd33b29f`, and `835d51562f73` are paused. Verify with `hermes cron list --all`; this repo-only slice does not resume them.

Nanobot should read recurring project/server evidence through the local server-safe read-only gateway (`http://127.0.0.1:18791/`) instead of receiving repeated copied packets. The gateway exposes allowlisted project evidence plus selected server context roots (`~/work`, user systemd units, selected Hermes/Nanobot docs/workspace/skills/cron, and local operator scripts), supports only GET/HEAD/OPTIONS, blocks traversal/hidden/secret-like/sensitive paths, blocks oversized or unsafe-extension files, and does not grant filesystem write permission. Workspace-local copied packets remain a fallback for one-off sanitized bundles. Do not give Nanobot raw `/`, `~/secure`, `.ssh`, `.codex`, browser profiles, live vault roots, or credential directories.

## Vault safety contract

Live vault mutation is allowed only through:

```text
observe → propose → review → explicit approval → backup → apply → verify
```

`tools/obsidian_apply.py` must refuse real edits unless an approval manifest is provided. The manifest must explicitly name the target vault, proposal file, target files, expected hashes, backup root, and approved change set.

Protected paths are not writable by adapters or workers:

- `.obsidian`
- `_Backups`
- `_Archive`
- `.trash`
- Soul-protected paths
- generated/cache/secret-bearing paths

## Graphify / indexing policy

- Graph-first before embedding-first.
- Graphify semantic work runs on sandbox copies first, not the live vault.
- Use Graphify's native workflow before proposal generation: build/extract to `graphify-out/`, read `GRAPH_REPORT.md`, then use `graphify query`, `graphify path`, or `graphify explain` for decisions. RAG counts are only a preflight/noise guardrail, not the main Graphify deliverable.
- External LLM traffic is governed by `docs/spec-kit/28-global-headroom-only-llm-channel.md`: Graphify uses `graphify-headroom` + `codex-cli` through Headroom; Nanobot external review uses `/home/hermesadmin/.nanobot-hermes/bin/nanobot-headroom-agent` with the Codex backend-shaped Headroom bridge and per-run Codex CLI auth inheritance.
- Embeddings are optional and later-stage only: small batches, default 50, hard cap `--max-files <= 75` per run, drain used swap before launch, single worker, `nice`/`ionice` where applicable, checkpoint/resume, and stop-on-load guardrails.
- No Graphify, MCP, RAG, or embedding component may directly write/delete/move notes in the live vault.

## Working conventions

- Use absolute paths in logs and reports.
- Keep generated artifacts under `out/` unless the task says otherwise.
- Keep local generated/cache/backup artifacts out of git via `.gitignore`.
- Root-level `obsidian_*.py` files are wrappers only; canonical implementation lives in `tools/` and shared policy lives in `src/obslayer/`.
- Prefer JSON for machine-readable bundles and Markdown for human reports.
- Keep reports concise and include exact commands, changed files, and verification results.


## Report path handling

Use absolute paths in internal logs/evidence when they are needed for verification. For sanitized handoff reports, release-facing summaries, or artifacts meant to leave the local operator context, redact or relativize raw live-vault, sandbox, derived-cache, and secret-bearing paths. Treat internal evidence, sanitized handoff reports, and public summaries as separate artifact classes.

## Verification policy

After any apply, run a fresh observation and compare it to the baseline. Stop on the first unexpected regression and report the mismatch clearly.

For docs-only changes, run at minimum:

```bash
git diff --check
```

When code, schemas, workflows, or runtime behavior changes, run the relevant project verification target, usually:

```bash
make verify
```
