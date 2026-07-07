# 26 — Nanobot Standing Maintenance and Communication Worker

Status: active operating procedure  
Date: 2026-07-02  
Scope: Nanobot as a standing worker for project maintenance, communication, and proposal routing

## Decision

Nanobot should participate in ongoing project operations, not only one-off Graphify work.

Nanobot is a standing worker and local communication hub for bounded maintenance tasks. It routes model calls through the localhost Headroom URL bridge when using Codex subscription inheritance. Hermes remains the orchestrator, safety owner, and acceptance owner.

```text
projects / repos / vault snapshots / reports
  ↓ observe/read-only
Nanobot standing worker
  ↓ task packets / status reports / proposals / handoff notes
Hermes acceptance gate
  ↓ approve / reject / ask user / create manifest / dispatch next worker
project docs / GitHub / Obsidian proposal pipeline
```

## Role split

| Role | Owner | Responsibilities |
|---|---|---|
| Orchestration and acceptance | Hermes | Task selection, safety gates, user communication, final approval, live apply decisions |
| Standing worker / hub | Nanobot | Routine read-only observation, task packet handling, graph/status/proposal drafts, inter-agent handoff notes |
| Code implementation | Codex/subagents | Non-trivial code changes when explicitly dispatched |
| External adapters | MCP/RAG/Graphify/tools | Read/search/analyze/graph/render/propose only |

Nanobot must not become an autonomous live operator. It is a supervised worker.

## Standing duties

Nanobot may be used for:

- project health snapshots;
- repository documentation drift checks;
- issue/PR/status summarization;
- Graphify semantic graph tasks;
- finding stale docs and TODO surfaces;
- preparing proposal-only cleanup bundles;
- converting worker output into handoff notes;
- routing small task packets between Hermes, Codex/subagents, and local adapters;
- maintaining a local queue state under `out/queue/` for project tasks;
- producing concise reports for Hermes to review.

## Forbidden duties

Nanobot must not:

- mutate the live Obsidian vault;
- apply proposals;
- move/delete/rename project files unless Hermes explicitly dispatches a reviewed repository task;
- start local embeddings automatically;
- start long-running/high-load jobs without a bounded task packet;
- change auth, credentials, tokens, provider state, profiles, cron jobs beyond the approved scout/reviewer loop, or server services;
- install GitHub Apps, enable paid services, publish, deploy, restart production, or expose network ports;
- read or print secrets.

## Operating modes

### 1. Observe mode

Read-only scan and status report.

Inputs:

- project root or sandbox snapshot;
- scope list;
- stop conditions.

Outputs:

- Markdown status report;
- optional JSON findings;
- no file changes outside `out/`.

### 2. Proposal mode

Convert observations into proposal-only artifacts.

Outputs:

- `proposal.json`;
- `proposal.md`;
- evidence list;
- no live apply.

### 3. Communication hub mode

Normalize handoff between workers.

Outputs:

- task packet;
- worker result summary;
- blocked/needs-user-decision note;
- acceptance checklist for Hermes.

### 4. Graphify mode

Use the dedicated Graphify contract in `25-nanobot-graphify-worker.md`:

- `gpt-5.4-mini`;
- subscription bridge;
- sandbox/read-only;
- graph-first;
- embeddings later only by separate approved slice.


## Approved scheduled review loop

Dmitry approved a bounded standing Nanobot review loop:

1. `212b7e8f3c21` — **Nanobot Obsidian Layer 15m audit scout**.
   - Script: `/home/hermesadmin/.hermes/scripts/nanobot_obslayer_scout.py`.
   - Schedule: every 15 minutes.
   - Delivery: local.
   - Output: `out/reports/nanobot-cron-scout/` and Nanobot→Hermes offers in `~/.nanobot-hermes/comm/hermes-inbox/`.
2. `f553d3d40ec9` — **Hermes Nanobot internal comm watcher**.
   - Script: `/home/hermesadmin/.hermes/scripts/nanobot_hermes_comm_watcher.py`.
   - Schedule: every 1 minute.
   - Delivery: local.
   - Output: ACK/reaction messages in `~/.nanobot-hermes/comm/nanobot-inbox/`.
3. `d2a5fd33b29f` — **Hermes lightweight review Nanobot scout reports**.
   - Script: `/home/hermesadmin/.hermes/scripts/nanobot_report_reviewer.py`.
   - Schedule: every 15 minutes.
   - Delivery: origin chat, but silent when there are no newly reviewed reports.
   - Output: `out/reports/nanobot-hermes-reviewer/` plus local reviewed-hash state in `~/.nanobot-hermes/comm/state/hermes_report_reviewer.json`.
4. `835d51562f73` — **Companion deep-review Nanobot scout backlog**.
   - Script: `/home/hermesadmin/.hermes/scripts/nanobot_deep_review_companion.py`.
   - Schedule: every 4 hours.
   - Delivery: origin chat.
   - Worker profile: `companion` (chosen because it has no current Kanban assignments; not `ops`).
   - Batch: bounded old/new scout report review, oldest-first, default 12 reports per run.
   - Output: `out/reports/nanobot-companion-deep-review/` plus local reviewed-hash state in `~/.nanobot-hermes/comm/state/companion_deep_reviewer.json`.

This loop closes the previous gap where Nanobot reports were ACKed but not reviewed. The lightweight reviewer is still script-only triage. The companion deep reviewer does separate-profile proposal-only classification (`duplicate`, `no-action`, `stale`, `actionable`, `blocker`) and synthesis. Both may summarize, flag action candidates, and point to evidence, but must not mutate repo/vault/auth/services, close cards, or apply docs without Hermes/Dmitry acceptance.

## Task packet contract

```json
{
  "task_id": "nanobot-maint-YYYYMMDD-...",
  "worker": "nanobot-standing-worker",
  "mode": "observe|proposal|communication_hub|graphify|scheduled_scout",
  "model": "gpt-5.4-mini",
  "source": {
    "kind": "repo|sandbox-vault|report-bundle|queue",
    "path": "..."
  },
  "allowed_capabilities": ["read", "search", "analyze", "summarize", "graph", "propose", "route"],
  "forbidden_capabilities": ["secret-read", "live-mutation", "direct-apply", "deploy", "restart", "cron-create-or-edit-except-approved-scout", "paid-action", "network-expose", "embedding-auto-run"],
  "outputs": {
    "report": "out/reports/.../report.md",
    "findings": "out/reports/.../findings.json",
    "proposal": "out/proposals/.../proposal.json"
  },
  "acceptance_owner": "Hermes",
  "requires_user_approval_for": ["live_apply", "new_or_changed_cron", "third_party_app", "paid_action", "deploy", "service_restart"]
}
```

## Queue integration

Standing tasks should use the local queue model from `07-local-queue-schema.md` when they need persistence:

```text
out/queue/pending → out/queue/running → out/queue/done|failed|blocked
```

Queue files are project artifacts, not live memory. They can be rebuilt or archived.

## Reporting cadence

Allowed without extra approval:

- on-demand reports when Hermes/user requests;
- reports generated during an active bounded project slice;
- local `out/` artifacts for verification.

Approved scheduled scout:

- Дмитрий approved one supervised Nanobot cron scout on 2026-07-04, then explicitly expanded it to a 15-minute bounded audit loop.
- Schedule target: `every 15m` via Hermes cron job `212b7e8f3c21`.
- Script: `/home/hermesadmin/.hermes/scripts/nanobot_obslayer_scout.py`.
- Delivery: `local`; reports are written under `out/reports/nanobot-cron-scout/`.
- Scope: Obsidian Operating Layer maintenance only; read-only evidence gateway only; report-only recommendations.
- The job may run Nanobot through `/home/hermesadmin/.nanobot-hermes/bin/nanobot-headroom-agent` and Headroom's backend Codex bridge.
- Scheduled audit runs use `/home/hermesadmin/.nanobot-hermes/config.audit.json` via `NANOBOT_CONFIG`; this selects the `codex-small` preset (`gpt-5.4-mini`, low reasoning) so 15-minute audits do not consume the default strong Nanobot model.
- The job uses a lock, timeout, sanitized raw output, preflight, `project-state.json`, and deterministic `docs-lag-audit/REPORT.md` to check whether docs/specs lag behind latest commits/proposals/reports.
- The job preflights the read-only evidence snapshot at `http://127.0.0.1:18791/snapshot.json`; Nanobot should start from that snapshot rather than guessing gateway URLs.
- The script supports `--dry-run` for preflight/docs-lag verification without an LLM/Nanobot call; `--help` must not trigger an audit.
- The job must not mutate the repo, live vault, auth, profiles, services, network exposure, deployments, or embeddings. Cron scope/schedule changes still require explicit user approval.
- Any blocked/quota/auth/provider result is a reportable blocker, not a reason to bypass Headroom or broaden access.

Requires explicit user approval before enabling/changing:

- additional cron jobs or schedule/scope/delivery changes to the approved scout;
- daemonized Nanobot service changes;
- scheduled Telegram/GitHub posting;
- background jobs that run indefinitely;
- high-volume or paid API usage.

## Acceptance checks for every Nanobot result

Hermes must verify before acting on a Nanobot result:

- scope stayed inside the task packet;
- no protected paths were targeted;
- no secrets appear in report/proposal artifacts;
- no live vault mutation happened;
- no service restart/deploy/auth mutation happened, and no cron mutation happened except the explicitly approved 15-minute scout definition;
- high-load jobs were not started unexpectedly;
- output has evidence and paths/hashes where relevant;
- proposal-only output is clearly separated from approved apply.

## Stop conditions

Stop and escalate to Hermes/user if Nanobot encounters:

- missing or ambiguous scope;
- secret-like material;
- live mutation request;
- production service/action request;
- paid/third-party permission request;
- high-load indexing/embedding request;
- conflicting worker results;
- inability to prove read-only behavior.

## Current accepted boundary

Accepted now:

- Nanobot as standing read-only/proposal/communication worker;
- Nanobot as Graphify worker through the separate contract;
- local reports/proposals under `out/`;
- Hermes review before any action.

Not accepted without separate approval:

- additional autonomous cron/schedules beyond the approved 15-minute local audit scout;
- live vault writes;
- production restarts/deploys;
- third-party GitHub App installs;
- paid/high-volume API usage;
- automatic embeddings;
- auth/profile/credential mutation.

## Model routing

For Codex-backed Nanobot work, use the localhost Headroom Codex backend bridge through the accepted wrapper rather than direct upstream calls.

- Accepted wrapper: `/home/hermesadmin/.nanobot-hermes/bin/nanobot-headroom-agent`
- Accepted URL: `http://127.0.0.1:8787/backend-api/codex/responses`
- Env override: `NANOBOT_OPENAI_CODEX_RESPONSES_URL`
- Default small/Graphify model: `gpt-5.4-mini`
- Scope: localhost-only, no public exposure

If the wrapper, backend bridge, or OAuth layer is unhealthy, standing tasks should be marked blocked and returned to Hermes. Do not silently fall back to direct upstream provider calls.

## Runtime fallback and evidence standard

Standing-worker tasks that require Codex subscription capacity must use the accepted `nanobot-headroom-agent -> Headroom backend Codex bridge` path. If the wrapper/bridge/OAuth layer is unhealthy, mark the task `blocked` unless the task packet explicitly permits `local_structural_only` fallback. Any fallback report must be clearly labeled as non-semantic/non-model-backed where applicable.

Minimum evidence for each Nanobot standing-worker result:

- task packet ID, mode, and immutable scope;
- source kind/path or sanitized excerpt bundle identifier;
- output artifact list and result pointer;
- pre/post mutation check method when a project/vault source is involved;
- secret-scan result for generated artifacts;
- protected-path target scan result;
- confirmation that no cron mutation beyond the approved scout, service restart, auth/profile mutation, deploy, paid action, network exposure, or embedding auto-run occurred;
- explicit blocked reason and required Hermes/user decision for blocked tasks.

Queue packets under `out/queue/` should use immutable task IDs, explicit status transitions, and result pointers to reports/proposals. Blocked queue items must name the decision needed before retry.

### 2026-07-04 manual scout runtime result

A manual run of the approved scout was attempted immediately after cron setup. Preflight passed, but the Codex/Headroom-backed Nanobot model call was blocked by provider capacity/quota/auth state. The scout script now treats quota/auth/provider-rejected text as `blocked` even when the Nanobot wrapper exits with return code `0`, and writes a blocked `REPORT.md` plus sanitized `nanobot.raw.md`.

Boundary remains unchanged: no fallback route may bypass Headroom, no broader localhost access is allowed, and no live vault/repo/service/auth/cron mutation is allowed from Nanobot. Hermes may continue local structural-only spec-kit work while the model-backed scout is blocked.

### 2026-07-04 15-minute audit expansion

Дмитрий explicitly requested that Nanobot run every 15 minutes and audit the project/docs for lag. Hermes updated existing job `212b7e8f3c21` instead of creating a second overlapping job.

Runtime boundary:

- schedule: `every 15m`;
- mode: Hermes cron `no_agent` script;
- delivery: `local`;
- output: `out/reports/nanobot-cron-scout/`;
- lock: prevents overlapping runs;
- timeout: bounded Nanobot call;
- report-only/proposal-only;
- blocked reports are valid outcomes for quota/auth/provider limits;
- canonical evidence snapshot: `http://127.0.0.1:18791/snapshot.json`;
- operator smoke mode: `/home/hermesadmin/.hermes/scripts/nanobot_obslayer_scout.py --dry-run` (no LLM/Nanobot call).

The 15-minute audit loop is complemented by deterministic repo-side docs lag checks via `tools/obsidian_project_docs_lag_audit.py` / `make project-docs-lag-audit`; this provides non-LLM evidence when Nanobot/provider capacity is blocked.
