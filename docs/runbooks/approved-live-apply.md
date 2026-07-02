# Runbook — Approved Live Apply

This runbook is only for a narrow live change that the operator explicitly approved.

## Preconditions

- Proposal has been reviewed and has a narrow target set.
- Approval manifest names the exact proposal file, vault root, and target set.
- Approval manifest uses the exact approval phrase: `APPROVE OBSIDIAN APPLY`.
- Backup location is inside `_Backups/obsidian-operating-layer`.
- `make verify` passes before apply.
- The operator explicitly approved this exact manifest; dry-run success is not approval.

## Dry-run pattern

```bash
make verify
python3 tools/obsidian_apply.py --proposal out/propose/proposal.json --out out/apply/dry-run.json
```

Expected:

- `status: dry-run`
- `target_relpaths` exactly match the reviewed proposal targets
- no files are changed
- no backup directory is created yet

## Approved apply pattern

```bash
python3 tools/obsidian_apply.py --proposal out/propose/proposal.json --approval-manifest out/propose/approval-manifest.json --apply --out out/apply/apply.json
```

Then run a fresh read-only observation/proposal verification pass:

```bash
make live-proposal-only
```

## Approval manifest requirements

The manifest must include:

- `proposal` or `proposal_path`: exact path to the proposal JSON passed to `--proposal`
- `approved: true`
- `approval_phrase: "APPROVE OBSIDIAN APPLY"`
- `task_id`, `approver`, `reason`
- `vault_root`: exact vault root from the proposal
- `targets`: exact target paths matching the proposal, no extra/missing targets
- `backup_root: "_Backups/obsidian-operating-layer"`
- `dry_run: false`
- `require_post_verify: true`
- a narrow `max_files_per_run`

## Required report

Report:

- changed files;
- backup path;
- approval manifest path;
- post-apply verification result;
- any drift;
- rollback path.

## Stop conditions

- approval manifest mismatch;
- backup failure;
- protected path target;
- post-apply verification mismatch;
- unexpected live vault changes;
- any target under `.obsidian`, `_Backups`, `_Archive`, `.trash`, or Soul-protected paths.
