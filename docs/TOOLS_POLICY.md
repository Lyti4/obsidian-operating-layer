# Tools Policy — Obsidian Operating Layer

## Default

Read-only first. Proposal-only before live apply. Verify before reporting success.

Exact per-tool mode, write surface, test and governing instruction are
authoritative in `docs/tools/INDEX.md`; family behavior lives under
`docs/tools/families/`.

## Allowed without extra approval

- Read repo docs/code relevant to the task.
- Run local tests/checks that do not mutate live vaults or services.
- Hermes may write repo docs/proposals/reports inside the project for the active scoped task.
- Codex may write repo code/docs/reports only inside an explicit bounded task packet.
- Nanobot may write proposal/report artifacts only under approved project paths for an explicitly scoped task.
- Use Codex for bounded repo implementation/review when scope is explicit.
- Use Nanobot for read-only/proposal/report workflows inside approved boundaries.

## Requires explicit approval

- Live Obsidian vault mutation.
- Deletion/move/rename of user data or backups.
- Cron/service install/restart/enable/disable.
- Network exposure/public posting/deployments.
- Account/OAuth/provider/cost-affecting changes.
- Broad access for workers outside approved workspace/evidence paths.
- Every `approved-write` invocation, including backfill report creation; follow
  the exact tool-linked runbook and approved output/state.

## Forbidden

- Printing or storing secrets, tokens, cookies, private keys, raw `.env`, auth JSON, browser profiles.
- Letting external adapters directly mutate the live vault.
- Treating worker reports as accepted without Hermes verification.
- Running an `approved-write` tool without its linked rollback-bearing runbook.

## Verification

For non-trivial changes, run the narrowest real check: targeted test, CLI smoke,
`git diff --check`, or direct artifact inspection. A tool change also updates
its registry row, family guide, test and `documentation impact` in the same slice.

## Approval manifest minimum

Live apply approval must bind the proposal file, vault root, exact target set, backup path, and expected hashes where applicable.
