# 2026-07-04 — Semantic proposal explanation UX

## Result

Improved `tools/obsidian_review_dashboard.py explain` for `semantic-query-proposal-only-report` proposals.

The explanation now includes:

- proposal-only mode;
- explicit `not applicable — proposal-only / no targets` approval phrase;
- live mutation authorization flag;
- summary counters;
- query intents;
- top semantic candidate notes;
- safety boundary.

## Commands

```bash
pytest tests/test_review_dashboard.py -q
python3 tools/obsidian_review_dashboard.py explain   --proposal out/proposals/semantic-query-reports/final468-operator-review-20260704T093433Z/proposal.json   --out out/proposals/semantic-query-reports/final468-operator-review-20260704T093433Z/EXPLANATION.md
make verify
git diff --check
```

## Artifact

- `out/proposals/semantic-query-reports/final468-operator-review-20260704T093433Z/EXPLANATION.md`

## Boundary

This is review UX only. It does not create edit targets, approval manifests, backups, applies, service changes, auth changes, or live vault mutation.
