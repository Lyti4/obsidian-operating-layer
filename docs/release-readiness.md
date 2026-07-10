# Release Readiness — Obsidian Operating Layer

Status: release gate checklist  
Scope: safe local Obsidian operating layer; no live vault mutation is approved by this document.

Current runtime and jobs: `docs/RUNTIME_STATUS.md`. Tool modes and all
approved-write runbooks: `docs/tools/INDEX.md`. This checklist does not turn a
generated report or historical acceptance note into current authority.

## Purpose

This document is the single go/no-go gate for deciding whether the project is ready for a bounded operational release.

## Release principle

A release is acceptable only when the system remains read-only-first and every
write path is explicit, reviewed and verified. Existing content is backed up;
new-file creation must be non-overwriting with an explicit rollback.

## Required green gates

- `make verify` passes: tests, lint, compile.
- `git diff --check` is clean.
- Safety contract is still true:
  - observe before propose;
  - apply defaults to dry-run;
  - existing-note live apply requires approval manifest;
  - manifest targets exactly match proposal targets;
  - existing targets are backed up before content edits;
  - approved new-report creation is exclusive and has delete-only rollback;
  - post-apply verify runs and fails closed on drift.
- Protected paths remain blocked:
  - `.obsidian`
  - `_Backups`
  - `_Archive`
  - `.trash`
  - Soul-protected paths
- External adapters remain sandbox/read-only/proposal-only unless explicitly wrapped by the safety core.
- Every `approved-write` registry row resolves to a rollback-bearing runbook.
- Sanitized reports do not expose secrets, live vault absolute paths, sandbox absolute paths, or derived cache paths.

## Go conditions

A release can move forward when:

1. all required green gates pass;
2. acceptance status is reflected in `docs/acceptance/index.md`;
3. operator runbooks are current enough for the intended workflow;
4. any known blocker has a documented mitigation or is out of scope.

## No-go conditions

Stop the release if any of these are true:

- tests/lint/compile fail;
- an existing-note edit bypasses the approval manifest, or any approved-write
  operation bypasses explicit approval and its linked runbook;
- proposal and manifest target binding is ambiguous;
- protected path checks are bypassed or stale;
- raw secrets/tokens/cookies/passwords appear in generated reports;
- a sandbox/indexing/MCP run mutates the live vault;
- docs claim a capability is accepted when evidence only proves sandbox/read-only behavior.
- a tracked tool is absent from `docs/tools/INDEX.md` or has a broken instruction/test link.

## Rollback / disable conditions

Disable or roll back the affected slice if:

- post-apply verification detects unexpected drift;
- backup creation fails;
- an adapter leaks absolute live paths or secrets;
- external MCP/RAG behavior changes its declared tool surface;
- indexing starts timing out without a sanitized partial report.

## Release classes

| Class | Meaning | Allowed actions |
|---|---|---|
| `docs-only` | Documentation/productization update | No vault mutation |
| `sandbox` | Disposable vault copy validation | Sandbox writes only |
| `proposal-only` | Live vault read + proposal generation | No live writes |
| `approved-live-apply` | Narrow live change with manifest | Backup, apply, verify required |
| `approved-report-create` | One new unique operator report | Explicit approval, exclusive create, verify, delete-only rollback |

## Current default release class

`proposal-only` for live Obsidian usage.  
`sandbox` for indexing/RAG/MCP validation.  
`approved-live-apply` requires separate explicit operator approval.
