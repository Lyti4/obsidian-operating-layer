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
- Report back to Telegram with `docs/telegram-summary-templates.md` so Dmitry gets exact paths and verification evidence without opening server-local files.
- Do not touch Gateway/systemd, secrets, payments, public posting, production restarts, or network exposure from this package.

## Common safe aliases

These aliases shorten routine acceptance commands. They are read-only, proposal-only, or sandbox-render flows; they do not install cron and do not perform live apply.

```bash
make dashboard-list PROPOSAL_ROOT=out/proposals
make field-slice-example VAULT=/tmp/approved-vault-subset FIELD_SLICE_OUT=out/field-slices/example
make render-diagrams DIAGRAM_OUT=out/diagrams/manual-acceptance REPORT_OUT=out/reports/manual-acceptance
make rag-benchmark RAG_SANDBOX=out/sandbox-vaults/rag-benchmark RAG_REPORTS=out/reports/rag-benchmark
make mcp-benchmark MCP_SANDBOX=out/sandbox-vaults/mcp-benchmark MCP_REPORTS=out/reports/mcp-benchmark
```

Use a disposable sandbox or approved subset for `field-slice-example` unless Dmitry explicitly wants a read-only scan of the full live vault.

## Scheduled reports

Scheduled observe/index reports are intentionally not installed by this project. Cron/systemd/webhook scheduling requires separate explicit approval that names the schedule, destination, retention, and rollback/disable command.
