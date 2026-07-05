# 31 — Operator Flow and Evidence-Gated Review Queue

Status: active design / proposal-only operating contract
Date: 2026-07-04
Scope: make the Agentic OS review layer explicit for Hermes, Nanobot, semantic proposal tooling, and operator acceptance.

## Purpose

This document turns the scattered orchestration backlog, semantic workflow, channel registry, and Nanobot scout outputs into one explicit operator flow.

It is an operating contract, not live-apply authorization. The queue coordinates evidence and review state; it does not mutate the live vault or services.

## Safety boundary

- `live_mutation_authorized: false` by default.
- Queue entries are evidence/review records, not edit permission.
- Nanobot may add/read proposal-only reports through approved channels, but Hermes remains acceptance owner.
- Any live vault change still requires: explicit approval manifest -> backup -> apply -> verify -> post-observe.
- Auth/profile/service/cron/network changes remain out of scope unless Dmitry explicitly approves the exact action.

## Operator flow

```text
intake signal
  -> evidence snapshot
  -> route selection
  -> proposal/report generation
  -> review queue entry
  -> Hermes acceptance check
  -> operator decision
  -> optional explicit approval manifest
  -> backup/apply/verify only after approval
```

### 1. Intake signal

Accepted signal sources:

- deterministic project checks (`make verify`, docs-lag audit, channel-registry verify);
- Nanobot read-only/proposal-only scout reports;
- Codex review reports and blocked wrapper reports from `~/.codex-hermes/comm/hermes-inbox/`;
- semantic query/review artifacts under `out/proposals/`;
- Hermes manual observations.

### 2. Evidence snapshot

Each promoted item must name concrete evidence:

- source report/proposal path;
- command or URL used to observe it;
- safety boundary;
- whether live vault mutation occurred (`false` unless explicitly recorded otherwise).

### 3. Route selection

Use the channel registry as the route map:

| Work type | Default route |
|---|---|
| local verification | local tools / pytest / make |
| Nanobot second opinion | `nanobot-headroom-agent` via Headroom backend bridge |
| evidence read for Nanobot | read-only evidence gateway `http://127.0.0.1:18791/` |
| semantic proposal generation | local repo tooling under `tools/` and `src/obslayer/` |
| Codex project-wide review | `hermes-codex-run --mode review` with no repo changes; Hermes triages findings into smaller tasks |
| live apply | blocked until explicit approval manifest |

### 4. Proposal/report generation

Generated artifacts should stay under:

```text
out/proposals/<capability>/<timestamp>/
out/reports/<capability>/<timestamp>/
```

Reports should be concise and include:

- verdict/status;
- source evidence;
- proposed next action;
- risk boundary;
- rollback/disable path when applicable.

### 5. Review queue entry

The Agentic OS review queue is a conceptual state machine. A future implementation may generate a JSON/Markdown index from existing `out/` artifacts, but the states are fixed here first.

States:

| State | Meaning | Exit condition |
|---|---|---|
| `observed` | signal/evidence exists | source path and boundary recorded |
| `triaged` | Hermes classified risk and scope | promote/hold/reject decision written |
| `proposal_drafted` | proposal-only artifact exists | candidate paths/changes are explainable |
| `review_ready` | operator can decide | evidence, tests, and safety boundary are present |
| `approved_for_manifest` | Dmitry approved exact candidate | approval manifest may be generated |
| `applied_verified` | approved apply completed | backup/apply/verify/post-observe evidence exists |
| `held` | not safe/actionable now | reason and revisit condition recorded |
| `rejected` | not useful or unsafe | reason recorded |

Default state transitions are conservative:

```text
observed -> triaged -> proposal_drafted -> review_ready
review_ready -> held | rejected | approved_for_manifest
approved_for_manifest -> applied_verified
```

No state transition grants live mutation by itself.

## Acceptance checklist for queue items

Before marking an item `review_ready`, Hermes should verify:

- source evidence path exists;
- generated proposal/report is under `out/`;
- `live_mutation_authorized: false` unless an approved manifest is explicitly in scope;
- candidate paths are evidence inputs, not implicit edit targets;
- tests or deterministic checks are listed;
- Nanobot output, if used, is treated as second opinion rather than authority.

## Current initial queue candidates

| Candidate | Current state | Evidence |
|---|---|---|
| Orchestrator consolidation spec | `review_ready` | `docs/spec-kit/30-orchestrator-operating-spec.md`, `docs/acceptance/index.md` |
| Working-note link hygiene apply/post-verify | `applied_verified` | `out/reports/working-note-link-apply/20260704T163336Z/REPORT.md`, post-verify reports |
| Next safe working-note disambiguation | `proposal_drafted` | `out/proposals/working-note-link-next-safe-disambiguation/20260704T170712Z/REPORT.md` |
| Nanobot internal comm channel | `review_ready` | `~/.nanobot-hermes/comm/hermes-inbox/`, `~/.nanobot-hermes/comm/nanobot-inbox/`, watcher cron local output |
| Codex internal comm channel | `review_ready` | `~/.codex-hermes/comm/codex-inbox/`, `~/.codex-hermes/comm/hermes-inbox/`, `tools/codex_hermes_comm.py` |
| Evidence-gateway generated indexes | `review_ready` pending live service restart approval | `src/obslayer/nanobot_readonly_evidence_gateway.py`, `tests/test_nanobot_readonly_evidence_gateway.py` |

## Implemented deterministic queue index

The first generated review-queue index command scans selected repo/out evidence artifacts and emits:

```text
out/reports/operator-review-queue/<timestamp>/queue.json
out/reports/operator-review-queue/<timestamp>/REPORT.md
```

Command:

```bash
python3 tools/obsidian_operator_review_queue.py --out-dir out/reports/operator-review-queue/<timestamp>/
```

The command is read-only, deterministic, and tested. It does not inspect the live vault directly and does not create approval manifests.


## Codex native runtime

Codex is made repo-native through `docs/spec-kit/33-codex-native-runtime.md`, `/home/hermesadmin/.codex-hermes/bin/hermes-codex-run`, schema-versioned task/report packets, and explicit separation from Nanobot's architecture scout channel. Nanobot may recommend Codex tasks; Hermes dispatches and accepts them.


## Agentic improvement loop

The review queue is the deterministic index for `docs/spec-kit/34-agentic-improvement-loop.md`. Nanobot findings, Codex reports, and local deterministic checks become queue items only after Hermes records evidence paths and a next step. Queue presence does not grant live mutation rights.
