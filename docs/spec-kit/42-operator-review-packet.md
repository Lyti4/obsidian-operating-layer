# 42 — Operator Review Packet

Status: accepted repo-only post-readiness review checkpoint
Date: 2026-07-06
Scope: turn dry-run proposal evidence into a human-readable operator review packet without creating approval authority

## Purpose

The operator review packet is the safe continuation point after repo-only proposal/readiness gates. It lets Hermes show Dmitry exactly what would be reviewed next, while preserving the rule that live vault mutation remains blocked until a separate explicit approval manifest exists.

It consumes repo-local `out/` evidence only. It does not scan or mutate the live Obsidian vault. It does not create an approval manifest. It does not grant apply authority.

## Contract

Output mode:

```text
obslayer.operator-review-packet.v1
```

Safety fields are always fixed to:

```yaml
live_mutation_authorized: false
approval_manifest_created: false
approval_manifest_authority: false
target_paths: []
apply_authority: none
```

## Behavior

- If the source dry-run proposal packet has zero `dry_run_proposals`, the packet status is `no_candidate` and the next step is to return to scoring/manual candidate selection. Hermes must not ask the operator to approve an empty apply.
- If dry-run proposals exist and the source packet has no safety findings, the packet status is `ready_for_human_review`. This means review can be shown to the operator; it is not approval.
- If the source packet authorizes live mutation, creates approval authority, exposes live targets, or leaves repo `out/`, the packet status is `blocked`.

## CLI

```bash
python tools/obsidian_operator_review_packet.py \
  --repo . \
  --proposal-packet out/reports/safe-auto-proposal-thresholds-v1/<run>/safe-auto-proposal-thresholds-v1.json \
  --out-dir out/reports/operator-review-packet/<run>
```

Optional readiness evidence can be cited with `--readiness-packet`, but it remains inert evidence and does not grant apply authority.

Grouped proposal evidence with top-level `targets` is also accepted when replacements live under `targets[].evidence.grouped_replacements[]`. Target paths and `vault_root` are treated as review context only; the output still keeps `target_paths: []` and `apply_authority: none`.

```bash
python tools/obsidian_operator_review_packet.py \
  --repo . \
  --proposal-packet out/proposals/remaining-link-same-vault-rule/20260706T152315Z/proposal-next5.grouped.json \
  --out-dir out/reports/operator-review-packet/grouped-next5-smoke
```

## Acceptance

- inputs and outputs stay under repo `out/`;
- zero-candidate source packets produce `no_candidate`, not approval pressure;
- live mutation / approval-manifest / apply authority flags are refused;
- output includes JSON plus `REPORT.md`;
- tests cover no-candidate, ready-for-review, blocked, path guardrail, and writer behavior.
