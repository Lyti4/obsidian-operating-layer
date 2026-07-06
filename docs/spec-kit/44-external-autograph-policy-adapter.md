# External Autograph Policy Adapter

## Scope

This artifact distills reusable safety and review policy from `smixs/autograph`
and `smixs/agent-second-brain` for Obsidian Operating Layer (OOL). It is a
repo-local policy artifact only: it does not grant live vault mutation authority.

Source evidence: `out/reports/external-repo-policy-extract-smixs/HERMES_ACCEPTANCE_REPORT.md`.

Machine-readable artifact: `src/obslayer/policies/external_autograph_policy.v1.json`
validated by schema `docs/spec-kit/schemas/external-autograph-policy.schema.json`.
Selector/scorer code should consume that artifact instead of duplicating the
allow/deny lists inline.

## Authority contract

- OOL stays observe/propose/review-first.
- Selector/scorer packets remain evidence-only unless a separate approval
  manifest explicitly authorizes apply.
- Default packet apply authority is `none`.
- Live vault mutation is not authorized by this adapter.
- Dedup and link-cleanup proposals default to `approved: false`.
- `approved: false` means no apply, even if an item is low risk.
- `approved: true` is only meaningful inside a separately reviewed operator
  approval manifest with target, hash, backup, and vault-root checks.

## Protected path denylist

Adapted from autograph vault walk skips plus OOL protected surfaces:

- `_Archive/`
- `_Backups/`
- `.trash/`
- `Soul/`, `Soul-`, `Soul_Vault/`, `Soul-Vault/`
- `Canonical/`, `canonical/`
- generated/cache/report surfaces that are not memory-note targets

Selector mapping:

- protected target or source surfaces classify as high risk;
- protected targets are denied from review item output;
- protected/cross-vault alias items classify as `manual_only_no_apply`;
- apply authority remains `none`.

## Generated report and noise denylist

Autograph noise words and OOL generated-report path rules are adapted as a
candidate-deny policy for generated operational evidence:

- generated path parts: `/reports/`, `graphify-out/`, `out/reports/`
- noise words: `TODO`, `FIX`, `NEW`, `UPDATED`, `Phase`, `Score`, `Vault`,
  `Health`, `Pricing`, `GRAPH_REPORT`

Selector mapping:

- report/navigation aliases are kept as display labels: `keep_alias_no_apply`;
- generated report paths are not promoted as link targets;
- generated report evidence stays readable evidence, not an apply target.

## Link resolution classes

Adapted from autograph graph/link cleanup behavior:

| Resolution | OOL classification | Risk | Apply authority |
|---|---|---:|---|
| exact path/title or unique suffix/stem target | `link_resolution_safe_candidate` | low | `none` |
| ambiguous target, missing target, or manual-review route | `link_resolution_manual_only` | medium | `none` |
| protected/archive/generated target | `link_resolution_denied` | high | `none` |
| blocked/refuse salvage with safe top candidate only | `blocked_refuse_salvage_manual_review` | medium | `none` |

Safe-candidate means “safe to show an operator first”; it does not mean safe to
apply automatically.

## Dedup action taxonomy

Adapted from autograph dedup policy:

| Action | Risk | Default approval | OOL apply authority |
|---|---:|---:|---|
| `manual_hold` | high | `false` | `none` |
| `keep_linked_layers` | medium | `false` | `none` |
| `merge_duplicate` | low | `false` | `manifest-approved` only after separate approval |
| `thin_crm_overlay` | medium | `false` | `manifest-approved` only after separate approval |

OOL stores this taxonomy in selector packet metadata so downstream review and
ops verification can inspect the same durable rule set.

## Output metadata contract

Relevant selector and alias-classifier outputs should expose:

- `source_policy.policy_id = external-autograph-policy-adapter.v1`
- `source_policy.policy_ref = docs/spec-kit/44-external-autograph-policy-adapter.md`
- `source_policy.rule_id`
- `classification`
- `risk`
- `apply_authority`

This metadata is evidence for operator review. It does not create an approval
manifest and does not authorize live mutation.
