# Operator Guide

## Workflow

1. Run `python tools/obsidian_observe.py --vault <vault> --out <observe.json>`.
2. Review the observation JSON/Markdown output.
3. Generate a proposal with `python tools/obsidian_propose.py --observe <observe.json> --out-dir <proposal-dir>`.
4. Dry-run apply with `python tools/obsidian_apply.py --proposal <proposal.json>`.
5. For live apply only, create an approval manifest that binds the exact proposal, vault root, and target set.
6. Run `python tools/obsidian_apply.py --proposal <proposal.json> --approval-manifest <approval.json> --apply --out <apply.json>`.
7. Run `python tools/obsidian_verify.py --observe <observe.json> --proposal <proposal.json>` and compare post-apply observation when available.
8. Write the final run report into Obsidian Reports.

## Approval manifest requirements

The manifest must contain:

- `approved: true`
- `proposal`: absolute or resolvable path to the exact proposal JSON used with `--proposal`
- `approval_phrase: "APPROVE OBSIDIAN APPLY"`
- `task_id`, `approver`, `reason`
- `vault_root`: exact vault root for the proposal
- `targets`: exact approved target paths; the set must match proposal targets 1:1
- `backup_root: "_Backups/obsidian-operating-layer"`
- `dry_run: false`
- `require_post_verify: true`

## Fail-closed rules

`tools/obsidian_apply.py` must refuse live edits when:

- no approval manifest is provided;
- manifest does not name the proposal file;
- manifest proposal path does not match `--proposal`;
- manifest vault root does not match proposal vault root;
- manifest target set differs from proposal target set;
- proposal targets `.obsidian`, `_Backups`, `_Archive`, `.trash`, or Soul-protected paths;
- backup root escapes the vault or differs from `_Backups/obsidian-operating-layer`;
- `max_files_per_run` is exceeded.

## Recommended operating mode

- Use dry-run by default.
- Keep changes small.
- Re-scan after every edit.
- Write final run reports into `Memory-Vault/Hermes/Reports/`.
- Do not touch Gateway/systemd, secrets, payments, public posting, production restarts, or network exposure from this package.
