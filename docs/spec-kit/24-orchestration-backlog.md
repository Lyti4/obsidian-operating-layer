# 24 — Orchestration Backlog

Status: active orchestration plan  
Date: 2026-07-02  
Scope: finish, harden, improve, and begin applying Obsidian Operating Layer layer by layer.

## Purpose

This backlog converts the architecture/spec/acceptance documents into an execution order for Hermes-as-orchestrator.

The project should advance through narrow, verifiable slices. Live Obsidian mutation stays gated by explicit approval manifests.

## Layer map and definition of done

| Layer | Definition of done | Current status | Next slice |
|---|---|---|---|
| Safety core | protected paths, approval manifest, backup, drift verify, fail-closed tests | baseline accepted | keep regression tests green |
| Observe/propose/verify/apply | stable CLI, JSON + Markdown artifacts, dry-run default | baseline accepted | smoke live read-only proposal flow |
| Review/operator UX | list/explain, review bundle, decision record, runbooks | mostly accepted | use on real proposal-only pass |
| Sandbox layer | disposable copies, protected-path exclusions, reset controls | baseline accepted | medium sandbox indexing probe |
| Indexing/MCP/RAG | guarded wrapper, sanitized reports, derived storage, batching/resume | sandbox/read-only accepted | diagnose medium/full sandbox timeout path |
| Docs/productization | release gate, acceptance index, runbooks, changelog | productization slice added | keep docs in sync after each slice |
| Application layer | proposal-only live operation, then approved narrow apply | P3 proposal-only pass green | optional narrow approved apply after explicit manifest |

## Execution rules

1. Start every slice with `make verify` unless the slice is docs-only and already verified in the same session.
2. Prefer sandbox/read-only/proposal-only over live apply.
3. Use Codex/subagents for complex code changes and Hermes for orchestration, review, docs, and acceptance.
4. Do not promote external adapters without an adapter-specific scorecard.
5. Every accepted slice must name evidence artifacts and rollback/disable conditions.

## Priority backlog

### P0 — restore and freeze current green baseline

- Keep `make verify` green.
- Review current uncommitted indexing/runtime changes.
- Ensure `git diff --check` stays clean.
- Decide whether the current indexing runtime changes are one commit or split commits.

### P1 — productization surface

- Maintain `docs/release-readiness.md` as the release go/no-go gate.
- Maintain `docs/acceptance/index.md` as the accepted boundary map.
- Keep short runbooks under `docs/runbooks/`.
- Add release notes under `docs/releases/` for each accepted slice.

### P2 — indexing runtime stabilization

- Reproduce the previous 3/5 indexed failure in a small sandbox.
- Add a clearer failure report for file-level indexing errors if missing.
- Run a medium sandbox probe.
- Run full sandbox indexing only after medium probe passes.
- Update `docs/spec-kit/20-indexing-runtime-acceptance.md` with evidence.

### P3 — first real usage without mutation

- Run live vault observation read-only.
- Generate a proposal-only bundle for one low-risk improvement/report.
- Review with dashboard/explain.
- Do not apply unless a separate approval manifest is explicitly approved.

### P4 — narrow approved apply

Only after P3 produces a useful proposal and the operator approves:

- create exact approval manifest;
- backup;
- apply;
- post-observe;
- verify drift;
- record release note and acceptance update.

### P5 — refactor and portability

- Parameterize hardcoded local paths where practical.
- Split `tools/obsidian_indexing_stdio_probe.py` into smaller modules after behavior is frozen.
- Add integration checks for critical make targets.
- Reduce wrapper duplication only if it simplifies maintenance without breaking operator muscle memory.

## Stop conditions

Stop and report instead of continuing if:

- `make verify` fails;
- a sanitized report leaks secrets or raw live/sandbox/derived absolute paths;
- an external adapter declares write/delete/move capability unexpectedly;
- live vault fingerprint changes during a read-only/sandbox/proposal-only slice;
- an approval manifest does not exactly match proposal targets.

## Reporting format

Use the concise operator format:

```text
Сделано: ...
Проверка: ...
Осталось: ...
Риск/блокер: ...
Следующий шаг: ...
```


### 2026-07-02 P3 live proposal-only pass

Result: green read-only/proposal-only run.

Evidence:
- `make verify` passed before the run.
- Observation/proposal/verification artifacts: `out/live-proposal-only-20260702T093117Z/`.
- Live vault scan observed 1048 Markdown files and related non-Markdown assets.
- Generated proposal stayed `mode: dry-run`, `dry_run_default: true`, `approval_required: true`, `risk_class: read_only_only`, with `0` targets.
- Verification returned `ok: true` and no issues.
- Post-run mtime check found `0` live vault files modified since run start.
- Generated artifacts had no secret-pattern hits.

Finding:
- The runbook used stale CLI flags/paths; updated to current `--observe`, `--out-dir`, and verify command behavior.
