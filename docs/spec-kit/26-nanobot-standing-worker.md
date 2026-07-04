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
- change auth, credentials, tokens, provider state, profiles, cron jobs, or server services;
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

## Task packet contract

```json
{
  "task_id": "nanobot-maint-YYYYMMDD-...",
  "worker": "nanobot-standing-worker",
  "mode": "observe|proposal|communication_hub|graphify",
  "model": "gpt-5.4-mini",
  "source": {
    "kind": "repo|sandbox-vault|report-bundle|queue",
    "path": "..."
  },
  "allowed_capabilities": ["read", "search", "analyze", "summarize", "graph", "propose", "route"],
  "forbidden_capabilities": ["secret-read", "live-mutation", "direct-apply", "deploy", "restart", "cron-create", "paid-action", "network-expose", "embedding-auto-run"],
  "outputs": {
    "report": "out/reports/.../report.md",
    "findings": "out/reports/.../findings.json",
    "proposal": "out/proposals/.../proposal.json"
  },
  "acceptance_owner": "Hermes",
  "requires_user_approval_for": ["live_apply", "cron", "third_party_app", "paid_action", "deploy", "service_restart"]
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

Requires explicit user approval before enabling:

- new cron jobs;
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
- no service restart/deploy/cron/auth mutation happened;
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

- autonomous cron/schedules;
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
- confirmation that no cron, service restart, auth/profile mutation, deploy, paid action, network exposure, or embedding auto-run occurred;
- explicit blocked reason and required Hermes/user decision for blocked tasks.

Queue packets under `out/queue/` should use immutable task IDs, explicit status transitions, and result pointers to reports/proposals. Blocked queue items must name the decision needed before retry.
