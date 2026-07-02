# Runbook — Proposal Review

Use this to inspect pending proposals before any apply.

## List proposals

```bash
python3 tools/obsidian_review_dashboard.py list --proposal-root out --json
```

## Explain one proposal

```bash
python3 tools/obsidian_review_dashboard.py explain --proposal out/propose/proposal.json --out out/propose/explain.md
```

## Review checklist

- Proposal target is narrow and expected.
- Risk class is accurate.
- Evidence is present.
- No protected paths are targeted.
- No secrets or credentials are included.
- The intended action is still necessary.

## Decision

- Approve only by creating an explicit approval manifest for the exact proposal and targets.
- Reject by recording the reason in the proposal notes or operator report.
- Do not infer approval from a successful dry-run.
