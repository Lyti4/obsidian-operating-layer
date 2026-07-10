# Runbook — Proposal Review

**Статус:** `active proposal-only`. Role authority:
`docs/agents/HERMES.md`; tool family:
`docs/tools/families/operator-control-plane.md`.

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

- A review verdict is evidence, not approval. After the human owner explicitly
  approves the exact proposal and targets, Hermes may prepare the manifest.
- Reject by recording the reason in the proposal notes or operator report.
- Do not infer approval from a successful dry-run.

No live rollback is needed for review. Correct or supersede only the proposal
artifact; any later apply follows `docs/runbooks/approved-live-apply.md`.
