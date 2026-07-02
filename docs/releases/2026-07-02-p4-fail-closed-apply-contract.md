# 2026-07-02 — P4 fail-closed apply contract hardening

Status: sandbox-only hardening slice. Live vault mutation remains blocked until Dmitry approves an exact manifest.

## Changes

- Approval manifests now require the canonical backup root: `_Backups/obsidian-operating-layer`.
- The example approval manifests include the current required fields: `proposal`, exact `vault_root`, exact `targets`, `dry_run: false`, `require_post_verify: true`, and narrow `max_files_per_run`.
- `obsidian_apply.py` now performs mandatory post-apply content verification after a live apply and records `post_verify` in the result JSON.
- Added fail-closed tests for wrong backup root, extra approved targets, missing approved targets, and post-apply verification output.

## Evidence

- `python3 -m pytest tests/test_guardrails.py tests/test_apply_rehearsal.py -q` passed.

## Safety

- Tests use disposable sandbox vaults under pytest temporary directories.
- No live Obsidian vault writes were performed.
