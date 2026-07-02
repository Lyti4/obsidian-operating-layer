# Runbook — Approved Live Apply

This runbook is only for a narrow live change that the operator explicitly approved.

## Preconditions

- Proposal has been reviewed.
- Approval manifest names the exact vault, proposal, and target set.
- Backup location is available.
- `make verify` passes before apply.

## Apply pattern

```bash
make verify
python3 tools/obsidian_apply.py   --vault /home/hermesadmin/Obsidian   --proposal out/propose/proposal.json   --approval-manifest out/propose/approval-manifest.json   --out out/apply
python3 tools/obsidian_observe.py --vault /home/hermesadmin/Obsidian --out out/post_observe
python3 tools/obsidian_verify.py --vault /home/hermesadmin/Obsidian --baseline out/observe/observation.json --current out/post_observe/observation.json --out out/verify
```

## Required report

Report:

- changed files;
- backup path;
- verification result;
- any drift;
- rollback path.

## Stop conditions

- approval manifest mismatch;
- backup failure;
- protected path target;
- post-apply verification mismatch;
- unexpected live vault changes.
