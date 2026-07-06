# 49 — Manifest Candidate Selector

Status: implemented repo-only selector
Date: 2026-07-06

## Purpose

`manifest-candidate-selector-v1` selects a narrow, reviewable queue of candidate lines from an existing operator review packet. It is evidence-only and proposal-only.

It does not create an approval manifest, approve apply, authorize target paths, or read the live Obsidian vault.

## Inputs

The selector accepts three repo-local JSON artifacts:

- candidate-volume operator packet JSON
- unified operator review index JSON
- operator review packet JSON

Inputs and outputs must resolve inside the repository and under `out/` or `docs/`. Symlink escapes are refused.

## Selection Rules

The selector reads `operator_review_packet.review_items` and selects at most five items where:

- `route` is `proposal_candidate`, `suggest`, or `proposal_only_ready`; or
- `route` is missing/empty and the item has `source_id` plus a proposed target field such as `proposed_link`, `target`, or `new_text`.

Items mentioning protected or denylisted areas in any candidate-driving field (`source_id`, `old_link`, `proposed_link`, `target`, or `new_text`) are excluded to `manual_review_exclusions`. Denylisted terms are `.obsidian`, `_Backups`, `_Archive`, `.trash`, `Soul`, `secure`, `credentials`, `auth`, and `browser profile`.

## Safety

The output includes fixed inert safety at the root and under `safety`:

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

- `blocked`: any input claims live mutation, approval manifest creation/authority, non-empty `target_paths`, or apply authority; or the unified index reports `blocked_count > 0` or `missing_artifacts > 0`.
- `ready_for_operator_review`: one or more candidates are selected and there are no blockers.
- `no_candidate`: no candidates are selected and there are no blockers.

## Output

The CLI writes:

- `manifest-candidate-selector.json`
- `REPORT.md`

The JSON mode is `obslayer.manifest-candidate-selector.v1` and includes source artifact paths, selected candidates, manual review exclusions, findings, next safe step, and inert safety fields.

## CLI

```bash
python3 tools/obsidian_manifest_candidate_selector.py \
  --repo . \
  --out-dir out/reports/manifest-candidate-selector/grouped-next5-smoke
```

Current smoke evidence uses only existing repo-local JSON artifacts and selects five candidates from `out/reports/operator-review-packet/grouped-next5-smoke/operator-review-packet.json`.
