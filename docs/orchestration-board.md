# Orchestration Board

**Статус:** `historical-mirror`. Этот большой Markdown-board содержит датированные
решения и прошлые evidence pointers; он не является текущей lifecycle или
runtime authority. Активные задачи: `.specify/feature.json` и соответствующий
`specs/*/tasks.md`. Текущий runtime: `docs/RUNTIME_STATUS.md`. Role contracts:
`docs/agents/`. Не возобновляйте описанные ниже jobs или applies по тексту этого
файла.

This board is the operator-facing control surface for advancing Obsidian Operating Layer without silently collapsing planning, implementation, review, and acceptance into one role.

## Сохранённая safety boundary

- Live Obsidian vault mutation is blocked until a concrete approval manifest is explicitly approved.
- Default mode remains read-only/proposal-only/dry-run.
- Protected paths stay blocked: `.obsidian`, `_Backups`, `_Archive`, `.trash`, and Soul-protected paths.
- Third-party GitHub Apps stay blocked until explicitly approved.


## Standing safe-pattern approval — link-prefix hygiene

Dmitry granted standing approval for recurring Obsidian link-hygiene applies that match the already-verified safe pattern:

- exact replacement against the current live target file;
- proposed target file exists under the same approved Memory vault namespace;
- protected paths are excluded (`.obsidian`, `_Backups`, `_Archive`, `.trash`, Soul-protected paths, secrets/auth/browser profiles);
- generated report/evidence surfaces are treated as noise/suppressed by default, not routine live-edit targets;
- each file is still applied through an approval manifest, approved backup namespace, and post-verify;
- batches stay bounded and stop on any readiness, hash, target, backup, or verification issue.

This is not approval for creates, deletes, renames, moves, archive rewrites, Soul/cross-vault retargeting, semantic/global replacements, or any destructive/high-risk operation.


## R13 Kanban/evidence tracking rule

For the active Obsidian Operating Layer continuation, Kanban DB is the only lifecycle-state source of truth. Markdown board files are generated mirrors; accepted docs hold policy/acceptance; `out/` holds evidence. Worker or subagent self-reports must be attached to card comments/events and independently verified before a card advances. Historical selector reports such as `grouped-next5` are not reusable approval manifests.

## Nanobot read-only review handoff

Standard mode for Nanobot review is **gateway + evidence packet**:

1. Hermes keeps Nanobot read-only/proposal-only and does not grant raw home/vault/secrets access.
2. Nanobot may read repo docs through the read-only evidence gateway at `http://127.0.0.1:18791/` (`/project-docs/`, `/spec-kit/`, `/reports/`, `/proposals/`, `/server-work/obsidian-operating-layer/`).
3. For important reviews Hermes also generates a compact packet with `tools/nanobot_review_packet.py`, including scope, forbidden actions, safe URLs, git status, and a bounded diff.
4. If Nanobot cannot access gateway URLs or loops on file access, Hermes records `Nanobot unavailable/no verdict` and falls back to local verification + Codex/Ops review; it must not broaden access to live vault/secrets.

## Исторический снимок lanes

| Lane | Owner role | Current state | Acceptance gate |
| --- | --- | --- | --- |
| P3 read-only/proposal-only | Worker + Hermes acceptance | Green repeatable `make live-proposal-only` target; candidate-volume operator packet added for the 20260706T182612Z evidence bundle | Live vault modified files = 0; verification JSON `ok: true`; candidate volume/risk packet reviewed before any live pilot |
| P3 manifest-candidate selector | Worker + Hermes acceptance | Repo-only selector smoke generated for grouped-next5; selected 5 inert candidates from existing JSON evidence | Separate explicit approval manifest still required before any live pilot; selector must not authorize targets |
| P4 narrow approved apply | Worker + independent review + Hermes acceptance | Sandbox apply-contract green; live apply not started | Exact manifest, explicit operator approval, backup, apply, post-verify |
| GitHub automation | GitHub-native checks + Hermes acceptance | Open PRs: 0; Renovate dashboard open; main checks green | Required checks stay minimal and green; advisory scans reviewed |
| Safety/release review | Independent reviewer + Hermes acceptance | Ongoing per slice | No stale runbook flags; fail-closed tests cover critical gates |
| External tools/MCP | Research worker + Hermes acceptance | Read/search/propose only | No direct write/delete/move/secret-read capability |


## Исторические blockers reviewer lanes

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

## Сохранённые repo-only slices

P4 manifest-review fixture added: `tests/fixtures/p4_manifest_review/` plus `tests/test_p4_manifest_review_fixture.py` prove live-like approval manifests fail closed when proposal paths, target lists, or vault roots drift. This remains sandbox-only and does not touch the live vault.

Nanobot recommendation decisions are now fixed in `docs/spec-kit/36-current-evidence-index.md`: the accepted current-slice pointers stay source-controlled, generated-artifacts evidence remains under `out/` only, unified queue/state/decision surface stays proposal-only, candidate scoring is accepted only as read-only/proposal-only, acceptance-gate synthesis is deferred, and any autonomous/live apply authority is rejected for the current scope.

- Standing link-prefix baseline is now a reusable read-only tool: `tools/obsidian_standing_safe_link_prefix_baseline.py`; latest live baseline evidence under `out/reports/standing-safe-link-prefix-baseline/live-current/` reports `allowed_count: 0`, `actionable_apply_items: 0`, and no live mutation authority.
- Closure: the standing-policy/baseline integration and R13 reconciliation are accepted and closed. Do not reopen `lane-schema-v1` or other accepted R1–R13 control-plane layers as the next slice. The next useful work is fresh selector/regeneration evidence for remaining broken/ambiguous link discovery, suppression, and operator review.

## Исторический Kanban snapshot

Kanban card `t_423691d1` (`generated-artifacts-registry-drift / docs_update`) is done: compact pointers are in `docs/spec-kit/36-current-evidence-index.md`, with evidence at `out/reports/kanban-triage-continuation/20260706T173514Z-generated-artifacts-registry-drift/REPORT.md`. Generated `out/` artifacts remain evidence only.

Next active slice `remaining-link-same-vault-rule-next5` was approved and applied: post-verify `passed` with 5 logical replacements, evidence at `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/POST_VERIFY.next5.grouped.md`. No standing authorization remains for further live apply.

Current repo-only continuation slice `operator-review-packet-grouped-proposal-support` is accepted after independent read-only review. It extends the operator review packet to read grouped same-vault proposal evidence and generated `out/reports/operator-review-packet/grouped-next5-smoke/REPORT.md` with 5 review items while preserving `apply_authority: none` and `target_paths: []`.

Repo-only slice `unified-operator-review-index-v1` is accepted after independent read-only review. It adds a pre-full-vault-indexing control panel over repo-local `out/` and docs evidence, with latest Hermes smoke at `out/reports/unified-operator-review-index/hermes-smoke/REPORT.md`: status `ready_for_operator_review`, 12 artifacts, 11 present, 1 missing, 0 blocked, fixed `apply_authority: none`, and `target_paths: []`.

Full-vault proposal-only indexing gate is accepted after independent read-only review. It was run read-only against `/home/hermesadmin/Obsidian` and fed into the unified index. Evidence: `out/live-proposal-only-20260706T182612Z/` plus `out/reports/unified-operator-review-index/full-vault-proposal-only-20260706T182612Z/REPORT.md`. Current regenerated result includes the candidate-volume packet and removes the stale missing JSON pointer: `ready_for_operator_review`, 14 artifacts, 14 present, 0 missing, 0 blocked, 11 proposal-only pointers, 2 ready/review JSON packets, fixed `apply_authority: none`, and `target_paths: []`. No approval manifest or live apply was created.

Candidate-volume/operator-review packet gate is implemented and generated at `out/reports/candidate-volume-operator-packet/full-vault-proposal-only-20260706T182612Z/REPORT.md`. It reports 447 protected hits, proposal targets `0`, empty `first_manifest_candidate_queue`, and fixed inert safety. It is review evidence only and does not select or authorize live targets.

Manifest-candidate selector gate is accepted after independent read-only review: `out/reports/manifest-candidate-selector/grouped-next5-smoke/HERMES_ACCEPTANCE.md` records inert safety, `selected_count: 5`, `missing_artifacts: 0`, focused 20-test pass, `git diff --check`, and full `make verify`; Codex review `manifest-selector-independent-review-20260707T044711Z.codex_report.json` passed with blockers `[]`.

Current active repo-only slice: Nanobot recommendation follow-up for index freshness and proposal-only labels. Scope is docs/source-index hygiene only: align `docs/acceptance/index.md`, `docs/spec-kit/36-current-evidence-index.md`, `docs/spec-kit/37-vault-automation-indexing-roadmap.md`, and this board so generated `out/` evidence remains discoverable without becoming source truth. Next gate before any new live pilot is a fresh selector/regeneration pass against current evidence; the reviewed grouped-next5 selector candidates are already applied/verified and must not be reused for a new manifest. Any new live pilot remains behind Dmitry's separate explicit approval, except the recorded standing safe-pattern link-prefix hygiene policy, which still requires manifest, backup, and post-verify gates.
