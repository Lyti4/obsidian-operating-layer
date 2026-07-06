# 45 — Remaining Link Suppression Gate

Status: accepted repo-only policy slice.

## Purpose

After exact/unique link cleanup, the remaining unresolved wikilinks should not keep re-entering apply queues when they are known non-apply surfaces.

This gate converts the remaining `broken` / `ambiguous` links into explicit policy buckets and suppresses the non-actionable buckets from future candidate-scorer / apply-pipeline runs.

## Source artifacts

- Triage module: `src/obslayer/remaining_link_triage.py`
- Triage CLI: `tools/obsidian_remaining_link_triage.py`
- Candidate scorer suppression input: `tools/obsidian_candidate_scorer.py --suppression-triage-json ...`
- Policy artifact: `src/obslayer/policies/external_autograph_policy.v1.json`
- Schema: `docs/spec-kit/schemas/external-autograph-policy.schema.json`
- Latest evidence: `out/reports/remaining-broken-ambiguous-triage-20260706T1410Z/HERMES_ACCEPTANCE_REPORT.md`

## Policy buckets

| Classification | Meaning | Apply authority |
|---|---|---|
| `generated_report_auto_keep` | Generated/report/audit/evidence links are historical evidence. Keep them and do not rewrite by default. | `none` |
| `protected_cross_vault_manual` | Soul/cross-vault/protected source files or links require explicit operator review. No automatic retarget/create. | `none` |
| `graphify_exact_path_preferred_no_apply` | Link already names a precise Graphify report path; resolver can prefer the exact path, but notes are not rewritten. | `none` |
| `real_broken_needs_target_discovery` | A non-generated unresolved link needs target discovery before any proposal. | `none` until a separate manifest exists |
| `ambiguous_needs_operator_disambiguation` | A non-generated ambiguous link needs operator disambiguation before any proposal. | `none` until a separate manifest exists |

## Safety contract

The suppression gate is intentionally evidence-only:

```text
live_mutation_authorized: false
approval_manifest_created: false
apply_authority: none
```

It may remove known non-actionable items from future apply queues, but it must not silently edit the live vault or create approval manifests.

## Pipeline

1. Build or refresh wikilinks index.
2. Run remaining-link triage:

```bash
python tools/obsidian_remaining_link_triage.py \
  --wikilinks-jsonl out/reports/per-vault-index/<run>/wikilinks.jsonl \
  --out-dir out/reports/remaining-broken-ambiguous-triage-<stamp>
```

3. Run candidate scorer with the suppression packet:

```bash
python tools/obsidian_candidate_scorer.py \
  --notes-index-jsonl out/reports/per-vault-index/<run>/notes-index.jsonl \
  --wikilinks-jsonl out/reports/per-vault-index/<run>/wikilinks.jsonl \
  --suppression-triage-json out/reports/remaining-broken-ambiguous-triage-<stamp>/remaining-link-triage-v1.json \
  --out-dir out/reports/candidate-scorer-v1/<stamp>
```

4. Continue selector/review only from the suppressed scorer packet.

## Acceptance criteria

- Triage summary reports `actionable_apply_items: 0` unless a separate target-discovery slice is opened.
- Candidate scorer records `suppression_gate.enabled: true` when a triage packet is supplied.
- Candidate scorer records `suppressed_links` and `suppression_gate.by_classification` for audit.
- Suppressed links do not enter `candidate_packets` / `scored_links`.
- Tests and `git diff --check` pass.

## Current accepted result

Latest fresh index after previous applies:

```text
broken: 87
ambiguous: 5
triaged items: 92
generated_report_auto_keep: 78
protected_cross_vault_manual: 9
graphify_exact_path_preferred_no_apply: 5
actionable_apply_items: 0
```

Candidate scorer with suppression should therefore produce no apply-authorized items from those buckets.

## Acceptance bundle for current gate

The current suppression-gate slice is unified into a repo-only acceptance bundle:

- bundle: `out/reports/remaining-link-suppression-gate-20260706T1420Z/acceptance-bundle.json`
- doctor report: `out/reports/remaining-link-suppression-gate-20260706T1420Z/acceptance-bundle-doctor/REPORT.md`

The doctor status is `accepted` with no findings. The bundle records Codex force review, Nanobot scheduled scout input, scorer/selector smoke evidence, specs, and verification checks. It does not authorize live mutation or create approval manifests.

## Follow-on target discovery

A repo-only target-discovery layer is now available for future leftovers that are explicitly classified as `real_broken_needs_target_discovery` or `ambiguous_needs_operator_disambiguation`.

Current evidence: `out/reports/remaining-link-target-discovery-20260706T1500Z/REPORT.md`. The current packet contains 92 policy-suppressed items and zero proposal candidates, so no live apply batch is opened from it. See `docs/spec-kit/46-remaining-link-target-discovery.md`.

## 2026-07-06 broader-vault hardening

A broader `/home/hermesadmin/Obsidian` scan showed that Soul-vault source files can produce high-confidence path repairs if only the target is checked. The triage gate is now fail-closed for protected source roots too (`Soul-Vault/`, `Hermes-Soul-Vault/`, `Soul-Organism-Graphify-Vault/`, and source paths containing `/Soul/`). These rows remain `protected_cross_vault_manual` and do not enter live apply.

Evidence:

- Index: `out/reports/per-vault-index/broader-20260706T151108Z/REPORT.md`
- Triage: `out/reports/remaining-broader-triage-20260706T151405Z-source-protected/remaining-link-triage-v1.json`
- Discovery: `out/reports/remaining-broader-target-discovery-20260706T151405Z-source-protected/remaining-link-target-discovery-v1.json`
