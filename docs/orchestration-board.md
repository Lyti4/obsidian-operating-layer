# Orchestration Board

This board is the operator-facing control surface for advancing Obsidian Operating Layer without silently collapsing planning, implementation, review, and acceptance into one role.

## Current safety boundary

- Live Obsidian vault mutation is blocked until a concrete approval manifest is explicitly approved.
- Default mode remains read-only/proposal-only/dry-run.
- Protected paths stay blocked: `.obsidian`, `_Backups`, `_Archive`, `.trash`, and Soul-protected paths.
- Third-party GitHub Apps stay blocked until explicitly approved.

## Active lanes

| Lane | Owner role | Current state | Acceptance gate |
| --- | --- | --- | --- |
| P3 read-only/proposal-only | Worker + Hermes acceptance | Green repeatable `make live-proposal-only` target | Live vault modified files = 0; verification JSON `ok: true` |
| P4 narrow approved apply | Worker + independent review + Hermes acceptance | Sandbox apply-contract green; live apply not started | Exact manifest, explicit operator approval, backup, apply, post-verify |
| GitHub automation | GitHub-native checks + Hermes acceptance | Open PRs: 0; Renovate dashboard open; main checks green | Required checks stay minimal and green; advisory scans reviewed |
| Safety/release review | Independent reviewer + Hermes acceptance | Ongoing per slice | No stale runbook flags; fail-closed tests cover critical gates |
| External tools/MCP | Research worker + Hermes acceptance | Read/search/propose only | No direct write/delete/move/secret-read capability |


## Current blockers from reviewer lanes

- **P4 blocker — backup root policy:** live apply must fail closed unless backups use the approved namespace `_Backups/obsidian-operating-layer`. Either code and tests must enforce that exact namespace or the runbook must explicitly accept a different policy.
- **P4 blocker — post-apply verification:** `require_post_verify` must have an enforceable acceptance contract. A live apply is not accepted until a fresh post-apply observation/verification proves only approved targets changed.
- **P4 blocker — manifest schema drift:** the approval manifest example and documented workspace layout must match the actual fields validated by `obsidian_apply.py`.
- **GitHub advisory backlog:** code scanning still has open Scorecard/Semgrep advisories; required checks are green, but advisory findings need triage before declaring release-ready.

## P4 live-apply gate checklist

A live apply may proceed only when all items are true:

1. A fresh proposal bundle exists from `make live-proposal-only`.
2. The proposal has a narrow non-zero target set selected by the operator.
3. The approval manifest names the exact vault root, proposal file, and target paths.
4. The manifest contains the exact phrase `APPROVE OBSIDIAN APPLY`.
5. Dry-run apply output is reviewed before real apply.
6. Backup path is created outside protected canonical memory paths.
7. Post-apply verification compares fresh observation against expected targets.
8. Any unexpected drift aborts and triggers rollback review.

## Merge / review policy for solo-maintainer mode

- Required GitHub approvals are disabled while there is no independent GitHub reviewer account.
- Required gates are CI-based: `verify / python-3.11`, `verify / python-3.12`, and `codeql / python`.
- Independent review remains an orchestration lane: subagent/Codex review summaries are advisory evidence, not GitHub-blocking approvals.
- Admin bypass should not be needed for normal PRs; if used, it must be called out as an explicit acceptance exception.
- Bot dependency PRs may auto-merge only when required checks are green and advisory findings are reviewed.
- Workflow/security changes require explicit mention of security scan outcome before merge.

## Next proposed slice

Prepare a P4 manifest-review fixture and test that proves live-like approval manifests fail closed when proposal paths, target lists, or vault roots drift. This remains sandbox-only and does not touch the live vault.
