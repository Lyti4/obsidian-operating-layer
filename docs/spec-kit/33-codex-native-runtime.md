# 33 — Codex Native Runtime

Status: active local contract
Date: 2026-07-04
Scope: make this repository low-friction and native for Codex without weakening Hermes acceptance or vault safety.

## Why this exists

Hermes asked Codex how it wants to work here. Codex answered that the repository policy is mostly good, but the host runtime currently blocks the internal Codex sandbox before shell commands can run:

```text
bwrap: Creating new namespace failed: Permission denied
```

Therefore the native path is: keep task packets and reports clean, put host-specific flags in one wrapper, scrub environment variables, and let Hermes verify every result.

## Canonical runner

Implementation task:

```bash
/home/hermesadmin/.codex-hermes/bin/hermes-codex-run   --repo /home/hermesadmin/work/obsidian-operating-layer   --mode implementation   --task ~/.codex-hermes/comm/codex-inbox/TASK_ID.task.json
```

Review-only task:

```bash
/home/hermesadmin/.codex-hermes/bin/hermes-codex-run   --repo /home/hermesadmin/work/obsidian-operating-layer   --mode review   --task ~/.codex-hermes/comm/codex-inbox/TASK_ID.task.json
```

Repo source for the runner:

```text
tools/hermes_codex_run.py
```

Installed operator path:

```text
/home/hermesadmin/.codex-hermes/bin/hermes-codex-run
```

## Current runtime strategy

The runner defaults to `workspace-write`, which keeps Codex repo-scoped while still allowing an inline report file for the wrapper to capture. This host also has a known Codex internal sandbox blocker:

```text
bwrap: Creating new namespace failed: Permission denied
```

When that blocker prevents repository commands from running, Hermes may use the documented fallback explicitly:

```bash
/home/hermesadmin/.codex-hermes/bin/hermes-codex-run \
  --repo /home/hermesadmin/work/obsidian-operating-layer \
  --mode review \
  --sandbox danger-full-access \
  --allow-danger-full-access \
  --task ~/.codex-hermes/comm/codex-inbox/TASK_ID.task.json
```

This fallback is never automatic and does not grant Codex extra task rights. The actual boundary is the outer runner and policy:

- canonical repo root only: `/home/hermesadmin/work/obsidian-operating-layer`;
- scrubbed environment: no token/key/secret/cookie/password variables;
- task packet must declare mode and scope;
- `danger-full-access` is never implicit and is refused unless `--sandbox danger-full-access` and `--allow-danger-full-access` are both present;
- review mode must leave no diff and is checked with a content snapshot, not only `git status`;
- live vault/auth/service/cron/network/public/paid actions remain blocked without explicit user approval;
- Hermes verifies before accepting.

When host sandboxing is fixed, the same runner should run without the danger fallback:

| Mode | Default Codex sandbox |
|---|---|
| implementation | `workspace-write` |
| review | `workspace-write` |

## Communication layout

```text
~/.codex-hermes/comm/
  codex-inbox/      # Hermes -> Codex task packets
  processing/       # runner-claimed task packets
  hermes-inbox/     # Codex/wrapper -> Hermes reports
  done/             # completed claimed packets
  failed/           # blocked/protocol-violating packets
  state/            # runner/watch logs and processed state
```

Machine schemas:

```text
schemas/codex_task.v1.json
schemas/codex_report.v1.json
```

## What Nanobot says and does

Nanobot is intentionally separate from Codex:

- Nanobot acts as a proactive architecture/review scout for the Agentic OS layer.
- It observes evidence through the read-only evidence gateway and project artifacts.
- It writes proposals/reports to `~/.nanobot-hermes/comm/hermes-inbox/`.
- Hermes ACKs Nanobot through `~/.nanobot-hermes/comm/nanobot-inbox/`.
- Nanobot may recommend that Hermes dispatch a Codex implementation/review task.
- Nanobot may not directly invoke Codex, approve patches, mutate repo/vault/auth/services, create cron, or bypass Hermes.

In the operator flow, Nanobot says **what looks worth improving** and Codex says **what code/review result it produced for a bounded task**. Hermes decides what is accepted.

## Done criteria for Codex work

- Task packet exists and matches `codex_task.v1`.
- Runner executes and produces a `codex_report.v1`, or the wrapper produces a blocked/failed `codex_report.v1`.
- Codex/wrapper report matches `codex_report.v1`.
- Review mode leaves no repository diff.
- Implementation mode has changed files listed in report.
- Hermes runs independent verification, normally `git diff --check` and `make verify` for code/runtime changes.


## Sandbox guard

The native runner defaults to `workspace-write`. `danger-full-access` is not an implicit fallback: it must be requested with both `--sandbox danger-full-access` and `--allow-danger-full-access` by the Hermes/operator layer after recording why the weaker sandbox is insufficient. Review mode still compares a content snapshot before and after the run and fails if any repo content/status changes.

Workspace-write review runs may be unable to write directly to `~/.codex-hermes/comm/hermes-inbox/` because that path is outside the repository sandbox. In that case Codex may return a `codex_report.v1` JSON object as the final message; the Hermes wrapper captures that inline report from the `last-message.md` output and writes it to Hermes inbox for normal processing. If Codex exits successfully without a report, the wrapper writes a blocked report and returns nonzero so Hermes does not hang or accept an unauditable run.
