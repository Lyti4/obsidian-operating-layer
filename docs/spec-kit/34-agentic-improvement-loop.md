# 34 — Agentic Improvement Loop

Status: active operating contract
Date: 2026-07-04
Scope: continuous improvement loop for Nanobot, Codex, and Hermes while building the Obsidian Operating Layer as an agentic OS.

## Purpose

This spec answers the operator question: Nanobot should continuously look for improvements, Hermes should collect and triage them, specs should capture accepted direction, and Codex should review or implement bounded repo tasks.

The loop is proposal-first. It does not authorize live vault mutation, auth/profile changes, service restarts, cron changes, public posting, paid actions, or network exposure.

## Roles

### Nanobot — scout / recommender

Nanobot may:

- observe allowed project evidence through the read-only evidence gateway;
- identify architecture risks, simplification opportunities, scale bottlenecks, docs lag, and missing verification;
- draft proposal-only reports under `out/reports/` or `out/proposals/`;
- recommend candidate Codex tasks.

Nanobot must not:

- dispatch Codex;
- accept patches;
- mutate repo, live vault, auth/profile, services, scheduled jobs, or network exposure;
- bypass Hermes acceptance.

### Hermes — collector / analyst / acceptance owner

Hermes must:

- collect Nanobot reports and deterministic local evidence;
- triage findings into accepted / held / rejected / blocked;
- convert accepted findings into spec-kit updates, queue entries, or bounded Codex task packets;
- verify every worker output before reporting success;
- request explicit Dmitry approval before any gated live action.

### Codex — implementation / review worker

Codex may:

- run bounded review-only sweeps over the repo;
- implement task-scoped repo changes when dispatched by Hermes;
- produce `codex_report.v1` reports with findings, changed files, tests, blockers, and suggested next tasks.

Codex must not:

- mutate outside the declared repo/task scope;
- treat review-only tasks as write permission;
- touch live vault/auth/profile/services/scheduled jobs/network/public/paid surfaces without explicit approval;
- print or store secrets.

## Canonical loop

```text
Nanobot scout report
  -> Hermes collects and triages
  -> Hermes records accepted direction in spec-kit / queue
  -> Hermes dispatches bounded Codex review or implementation task
  -> Codex returns report / patch / blocker
  -> Hermes verifies locally
  -> Hermes updates review queue and acceptance evidence
  -> Dmitry decides on any gated/live action
```

## Intake sources

Accepted inputs:

- Nanobot scout reports from `out/reports/nanobot-cron-scout/`;
- Codex reports from `~/.codex-hermes/comm/hermes-inbox/`;
- deterministic checks: `make verify`, docs-lag audit, channel-registry verify;
- Hermes manual observations;
- proposal-only artifacts under `out/proposals/`.

## Codex project-wide sweep policy

Project-wide Codex sweeps are useful for agentic OS design review, but they must run as review-only tasks:

- `mode: review` in `codex_task.v1`;
- repo root fixed to `/home/hermesadmin/work/obsidian-operating-layer`;
- no repo content/status changes allowed by the wrapper;
- output must be a report, not an applied patch;
- Hermes converts accepted findings into smaller implementation tasks.

Current blocker evidence: a project-wide Codex review task was created and safely attempted, but Codex provider usage was exhausted. The wrapper produced a blocked report instead of bypassing limits or weakening safety.

Evidence:

```text
~/.codex-hermes/comm/codex-inbox/agentic-os-project-wide-review-20260704.task.json
~/.codex-hermes/comm/hermes-inbox/agentic-os-project-wide-review-20260704.wrapper-20260704T193616Z.report.json
```

Blocker:

```text
usage limit; retry after provider window resets or after account/credits upgrade
```

## Triage states

| State | Meaning | Next action |
|---|---|---|
| `accepted` | Hermes agrees finding is useful and safe | spec/queue/task update |
| `held` | useful but missing evidence or too broad | collect evidence / narrow scope |
| `rejected` | not aligned or unsafe | record reason if needed |
| `blocked` | external/runtime/provider blocker | retry later or use local deterministic path |
| `needs_approval` | requires live/gated action | ask Dmitry before proceeding |

## Done criteria

A loop iteration is done only when:

- source report/task path is recorded;
- Hermes triage decision is recorded;
- accepted items are represented in spec-kit, queue, or bounded task packets;
- verification command output is captured;
- no live/gated action happened without explicit approval.


## Runtime safety note

Sandbox fallback is explicit, not automatic. If Codex native isolation fails and Hermes must use `danger-full-access`, the wrapper requires an explicit operator flag and review-mode content snapshot verification still applies.
