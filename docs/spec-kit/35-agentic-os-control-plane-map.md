# 35 — Agentic OS Control Plane Map

Status: active operator index
Date: 2026-07-05
Scope: single cross-link surface for the Obsidian Operating Layer control plane: orchestrator spec, review queue, agent channels, runtime, acceptance, and improvement loop.

## Purpose

Nanobot repeatedly flagged that the new operator-flow, review-queue, Codex/Hermes channel, native runtime, and improvement-loop surfaces were landing faster than one canonical index/acceptance surface. This document is that index.

It is not live-apply authorization. It only maps evidence and handoff points so Hermes can triage, Codex can work bounded tasks, Nanobot can recommend safely, and Dmitry can see the current control plane in one place.

## Control-plane surfaces

| Surface | Role | Canonical evidence |
|---|---|---|
| Orchestrator operating spec | first-read policy and operating boundary for Hermes | `docs/spec-kit/30-orchestrator-operating-spec.md` |
| Evidence-gated review queue | shared proposal/report triage state and no-live-mutation boundary | `docs/spec-kit/31-operator-flow-and-review-queue.md`, `tools/obsidian_operator_review_queue.py`, `src/obslayer/operator_review_queue.py` |
| Codex ⇄ Hermes communication channel | local task/report/ACK protocol and role contract | `docs/spec-kit/32-codex-hermes-communication-channel.md`, `tools/codex_hermes_comm.py`, `schemas/codex_task.v1.json`, `schemas/codex_report.v1.json` |
| Codex native runtime | bounded repo-native execution lane and explicit sandbox fallback policy | `docs/spec-kit/33-codex-native-runtime.md`, `tools/hermes_codex_run.py`, `/home/hermesadmin/.codex-hermes/bin/hermes-codex-run` |
| Agentic improvement loop | Nanobot scout → Hermes triage → spec/queue → Codex task → Hermes verification loop | `docs/spec-kit/34-agentic-improvement-loop.md` |
| Acceptance surface | accepted/limited/not-yet-accepted capability map | `docs/acceptance/index.md` |
| Channel registry | machine-readable route/rights map | `docs/spec-kit/channel-registry.json`, `docs/spec-kit/29-channel-registry.md` |
| Docs lag gate | deterministic marker audit for drift | `tools/obsidian_project_docs_lag_audit.py`, `src/obslayer/project_docs_lag_audit.py` |

## Canonical flow

```text
Nanobot scout report / deterministic check / Codex report / Hermes observation
  -> evidence path recorded
  -> operator review queue item
  -> Hermes acceptance decision
  -> bounded Codex task only when useful
  -> local verification
  -> acceptance/index update when capability is accepted
  -> Dmitry approval before any live/gated action
```

## Queue state model

Use one shared vocabulary across reports, proposals, and acceptance:

| State | Meaning | Live mutation? |
|---|---|---|
| `candidate` | signal exists but evidence is incomplete | no |
| `proposal_drafted` | proposal/report exists and awaits triage | no |
| `review_ready` | evidence exists and Hermes can accept/hold/reject | no |
| `accepted_repo_only` | repo/docs/tooling capability accepted after verification | no live vault mutation |
| `applied_verified` | explicitly approved apply was backed up, applied, and verified | only if approval manifest exists |
| `held` | waiting on missing evidence, risk review, or operator decision | no |
| `blocked` | cannot proceed until stated blocker clears | no |
| `rejected` | not part of the accepted operating surface | no |

## Acceptance gates

A control-plane change is accepted only when all applicable gates are true:

1. evidence path exists and is named in the queue/report;
2. safety boundary states `live_mutation_authorized: false` unless there is an explicit approval manifest;
3. relevant spec-kit document links the source protocol/tool;
4. `docs/acceptance/index.md` records accepted/limited/not-yet-accepted status;
5. deterministic checks pass (`make verify`, docs lag audit, channel registry verify when relevant);
6. Hermes verifies worker output instead of relying on Nanobot/Codex self-report.

## Current Nanobot synthesis

Across the Nanobot scout reports reviewed on 2026-07-05, the repeated signal was:

- core documented loops are mostly healthy/current;
- the newest 30–34 spec set, operator queue, and Codex/Hermes runtime surfaces needed one canonical map;
- acceptance/index drift should be machine-checked rather than inferred from repeated reports;
- Nanobot remains scout/recommender only; Hermes remains acceptance owner; Codex remains bounded implementation/review worker.

This map closes the repeated “single operator/control-plane surface” recommendation and gives the docs lag audit a stable marker to check.

## Boundary

This document is repo documentation only. It does not authorize live vault mutation, auth/profile changes, service restarts, cron changes, public network exposure, public posting, or paid/high-volume actions.
