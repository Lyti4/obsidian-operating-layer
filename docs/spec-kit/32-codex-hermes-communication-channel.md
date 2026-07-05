# 32 — Codex ⇄ Hermes Communication Channel

Status: active local contract
Date: 2026-07-04
Scope: explicit communication, roles, and rights for using Codex as implementation/review worker under Hermes orchestration.

## Purpose

Codex is the primary coding/review executor for non-trivial implementation work. This channel makes the interaction explicit and auditable instead of relying only on terminal transcripts.

The channel is local/server-side. It is not user Telegram and it is not a live-apply permission path.

## Paths

| Direction | Path |
|---|---|
| Hermes → Codex task packets | `~/.codex-hermes/comm/codex-inbox/` |
| Codex → Hermes reports | `~/.codex-hermes/comm/hermes-inbox/` |
| Claimed tasks | `~/.codex-hermes/comm/processing/` |
| Completed task packets | `~/.codex-hermes/comm/done/` |
| Failed / protocol-violating task packets | `~/.codex-hermes/comm/failed/` |
| State / processed reports | `~/.codex-hermes/comm/state/` |
| Role policy | `~/.codex-hermes/docs/ROLE_POLICY.json`, `~/.codex-hermes/docs/ROLE_POLICY.md` |

Canonical helper:

```text
tools/codex_hermes_comm.py
```

Hermes wrapper:

```text
/home/hermesadmin/.hermes/scripts/codex_hermes_comm.py
```

Native runner:

```text
/home/hermesadmin/.codex-hermes/bin/hermes-codex-run
```

Repo source:

```text
tools/hermes_codex_run.py
```

Task/report schemas:

```text
schemas/codex_task.v1.json
schemas/codex_report.v1.json
```


## Roles

### Hermes

Role: `orchestrator_acceptance_owner`.

Hermes may:

- write bounded task packets;
- read Codex reports;
- ACK reports back to Codex;
- verify changed files/tests;
- accept, reject, or hold findings;
- request Dmitry approval for gated actions.

Hermes must:

- state task scope and rights in every task packet;
- enforce `AGENTS.md`, channel registry, and approval-manifest gates;
- sanitize secrets;
- verify outcomes before reporting success.

### Codex

Role: `bounded_implementation_and_review_worker`.

Codex may:

- read repository task scope;
- propose patches;
- implement repo-scoped code/docs when dispatched;
- run relevant tests inside scope;
- write reports to Hermes inbox.

Codex must:

- stay inside `/home/hermesadmin/work/obsidian-operating-layer` unless a task explicitly adds another path;
- treat live vault as read-only unless Dmitry has approved an exact manifest;
- return changed files, tests, blockers, and exact commands run;
- never print/store secrets.

## Rights boundary

| Surface | Default right |
|---|---|
| Repo read | allowed inside task scope |
| Repo write | allowed only for implementation tasks and only inside active task scope |
| Review-only tasks | no repo writes |
| Live vault mutation | forbidden without explicit approval manifest, backup, apply, verify |
| Auth/profile mutation | forbidden without explicit user approval |
| Service restart / deploy / cron / network exposure | forbidden without explicit user approval |
| Secrets | redact/no-print/no-store |
| Public posting / paid actions | forbidden without explicit user approval |

## Protocol

Hermes task packet command:

```bash
python3 tools/codex_hermes_comm.py task   --type implementation   --instructions "..."
```

Codex report command:

```bash
python3 tools/codex_hermes_comm.py report   --task-id <task-id>   --status ok   --summary "..."   --changed-file path   --test "pytest ..."
```

Hermes ACK command:

```bash
python3 tools/codex_hermes_comm.py watch
```

Self-test:

```bash
python3 tools/codex_hermes_comm.py selftest
```

## Scheduling boundary

No Codex channel cron job is installed by default. Hermes runs `watch` after Codex work or during an active orchestration session. Any durable background watcher/cron for Codex requires explicit user approval.

## Acceptance

A Codex report is not accepted until Hermes verifies it. If Codex changes code, Hermes must run relevant tests and usually `make verify` before reporting success.


## Codex native runtime

Codex was asked for its preferred setup. It requested one stable Hermes runner that hides host-specific flags and consumes versioned JSON task packets. That runner is defined in `docs/spec-kit/33-codex-native-runtime.md`.

Current host caveat: Codex internal sandboxing can fail with `bwrap: Creating new namespace failed: Permission denied`. Until fixed, Hermes may choose the documented fallback only by passing both `--sandbox danger-full-access` and `--allow-danger-full-access`; the runner never falls back implicitly. That fallback remains behind the outer Hermes boundary: scrubbed env, canonical repo root, review-only no-diff enforcement, blocked reports for protocol failures, and Hermes verification.

## Nanobot relationship

Nanobot remains a separate proactive architecture/review scout. It says what should be improved, simplified, or scaled; Hermes may convert that into a bounded Codex task. Nanobot does not call Codex directly, approve Codex work, or mutate live surfaces. Its channel is `~/.nanobot-hermes/comm/`; Codex's channel is `~/.codex-hermes/comm/`.


## Runner sandbox boundary

Codex task packets do not grant live-surface rights. The Hermes runner defaults to `workspace-write`; `danger-full-access` requires both `--sandbox danger-full-access` and an explicit `--allow-danger-full-access` operator flag, and remains bounded by task policy plus Hermes verification.

When sandboxed Codex cannot write the out-of-repo Hermes inbox directly, the wrapper treats a final inline `codex_report.v1` JSON message as the report transport and persists it server-side. If Codex exits without a report, times out, fails, or mutates a review-only workspace, the wrapper writes a blocked/failed `codex_report.v1` itself instead of leaving Hermes waiting for an artifact. This keeps Codex repo-scoped while preserving the Hermes report channel.
