# Release Readiness — Obsidian Operating Layer

Status: release gate checklist  
Scope: safe local Obsidian operating layer; no live vault mutation is approved by this document.

## Purpose

This document is the single go/no-go gate for deciding whether the project is ready for a bounded operational release.

## Release principle

A release is acceptable only when the system remains read-only-first and every write path is explicit, reviewed, backed up, and verified.

## Required green gates

- `make verify` passes: tests, lint, compile.
- `git diff --check` is clean.
- Safety contract is still true:
  - observe before propose;
  - apply defaults to dry-run;
  - live apply requires approval manifest;
  - manifest targets exactly match proposal targets;
  - backup is created before any live write;
  - post-apply verify runs and fails closed on drift.
- Protected paths remain blocked:
  - `.obsidian`
  - `_Backups`
  - `_Archive`
  - `.trash`
  - Soul-protected paths
- External adapters remain sandbox/read-only/proposal-only unless explicitly wrapped by the safety core.
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
- a tool can mutate the live vault without an approval manifest;
- proposal and manifest target binding is ambiguous;
- protected path checks are bypassed or stale;
- raw secrets/tokens/cookies/passwords appear in generated reports;
- a sandbox/indexing/MCP run mutates the live vault;
- docs claim a capability is accepted when evidence only proves sandbox/read-only behavior.

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

## Current default release class

`proposal-only` for live Obsidian usage.  
`sandbox` for indexing/RAG/MCP validation.  
`approved-live-apply` requires separate explicit operator approval.
