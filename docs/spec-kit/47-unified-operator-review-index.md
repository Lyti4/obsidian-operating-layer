# 47 — Unified Operator Review Index

Status: implemented repo-only control panel
Date: 2026-07-06

## Purpose

`unified-operator-review-index-v1` gives Hermes/Dmitry one deterministic repo-local view of the latest safe evidence before scaling toward live full-vault indexing. It aggregates pointers and inferred status from `out/` artifacts and source-controlled docs.

This is a pre-full-vault-indexing control panel only. It is not an approval manifest, does not approve apply, and does not grant live vault mutation authority.

## Inputs

The builder accepts a repo root and an optional explicit artifact list. Without explicit artifacts, it checks the current known evidence pointers:

- `out/reports/operator-review-packet/grouped-next5-smoke/operator-review-packet.json`
- `out/reports/operator-review-packet/grouped-next5-smoke/REPORT.md`
- `out/reports/remaining-link-suppression-gate-20260706T1420Z/HERMES_ACCEPTANCE_REPORT.md`
- `out/reports/remaining-broader-target-discovery-20260706T152315Z-same-vault-rule/REPORT.md`
- `out/reports/per-vault-index/` machine-readable or report files, as pointer-only entries
- `docs/acceptance/index.md`
- `docs/spec-kit/36-current-evidence-index.md`

Inputs fail closed unless they resolve inside the repo and under `out/` or `docs/`. Symlink escapes are refused.

## Output

The CLI writes:

- `unified-operator-review-index.json`
- `REPORT.md`

The JSON mode is `obslayer.unified-operator-review-index.v1` and includes:

- `mode`, `generated_at`, `repo_root`, `status`
- `artifacts[]` with path, kind, existence, inferred status, inferred review item count, inferred safety flags, and notes
- `summary` counts for total, present, missing, ready-for-human-review, blocked, and proposal-only artifacts
- fixed inert `safety`
- `next_gates[]`

The fixed safety block is always:

```json
{
  "live_mutation_authorized": false,
  "approval_manifest_created": false,
  "approval_manifest_authority": false,
  "apply_authority": "none",
  "target_paths": []
}
```

## Status Rules

- `blocked`: any included JSON artifact claims live mutation, approval manifest, or apply authority.
- `ready_for_operator_review`: at least one proposal/review artifact is present and no blockers are found.
- `no_current_artifacts`: no proposal/review evidence is present.

Missing requested artifacts are counted but are not blockers.

## CLI

```bash
python3 tools/obsidian_unified_operator_review_index.py \
  --repo . \
  --out-dir out/reports/unified-operator-review-index/smoke
```

Use `--artifact PATH` repeatedly to build from an explicit artifact list.
## Latest full-vault proposal-only gate

The latest full-vault gate used the existing read-only/proposal-only Make target, then fed the generated artifacts into this index:

```bash
make live-proposal-only
python3 tools/obsidian_unified_operator_review_index.py \
  --repo . \
  --out-dir out/reports/unified-operator-review-index/full-vault-proposal-only-20260706T182612Z \
  --artifact out/live-proposal-only-20260706T182612Z/observation.json \
  --artifact out/live-proposal-only-20260706T182612Z/propose/proposal.json \
  --artifact out/live-proposal-only-20260706T182612Z/verify.json
```

Accepted boundary: this reads the live vault for observation only and writes repo-local `out/` evidence. It must not create an approval manifest or mutate the vault. The current regenerated result is `ready_for_operator_review` with 14 artifacts, 14 present, 0 missing stale pointers, 0 blocked artifacts, 11 proposal-only pointers, 2 ready/review JSON packets, and inert safety flags.

Follow-on gate: `docs/spec-kit/48-candidate-volume-operator-packet.md` distills the same repo-local observation/proposal/verify/unified evidence into candidate volume, protected bucket counts, and route buckets before any live pilot discussion. Its JSON and REPORT are now part of the default unified control-panel artifact set.

Next selector gate: `docs/spec-kit/49-manifest-candidate-selector.md` uses the unified index as a blocker check. The selector blocks if this index reports any blocked or missing artifacts, and otherwise selects at most five inert operator-review candidates from repo-local evidence.
