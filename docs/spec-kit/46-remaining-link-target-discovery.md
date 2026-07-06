# 46 — Remaining Link Target Discovery

Status: accepted repo-only discovery layer.

## Purpose

After exact-link cleanup and remaining-link suppression, only links explicitly classified as target-discovery/disambiguation candidates may be considered for future live repair.

This layer reads:

- `remaining-link-triage-v1.json`
- `notes-index.jsonl`

and emits a proposal-only discovery packet. It never edits the live vault, never creates approval manifests, and never grants apply authority.

## Safety contract

```text
live_mutation_authorized: false
approval_manifest_created: false
apply_authority: none
```

Suppressed policy classes remain suppressed:

- `generated_report_auto_keep`
- `protected_cross_vault_manual`
- `graphify_exact_path_preferred_no_apply`

Only these classes are eligible for discovery scoring:

- `real_broken_needs_target_discovery`
- `ambiguous_needs_operator_disambiguation`

A high-confidence match can become only a `proposal_candidate`; it still requires a separate manifest, backup, dry-run, readiness check, Codex/Nanobot review, live apply, and post-verify.

## CLI

```bash
python tools/obsidian_remaining_link_target_discovery.py \
  --triage-json out/reports/remaining-broken-ambiguous-triage-<stamp>/remaining-link-triage-v1.json \
  --notes-index-jsonl out/reports/per-vault-index/<stamp>/notes-index.jsonl \
  --out-dir out/reports/remaining-link-target-discovery-<stamp>
```

## Current accepted result

On the latest triage packet, all remaining items are policy-suppressed/report/protected/Graphify exact-path cases, so target discovery produces no live candidates.

```text
proposal_candidates: 0
apply_authority: none
live_mutation_authorized: false
```

## Broader vault result — 2026-07-06

A broader read-only scan across `/home/hermesadmin/Obsidian` produced many unresolved links, but after source-protected triage hardening there are no live-ready proposal candidates:

```text
notes: 541
wikilinks: 7214
ambiguous: 436
broken: 5452
proposal_candidates: 0
protected_cross_vault_manual: 5542
generated_report_auto_keep: 246
ambiguous_needs_operator_disambiguation: 100
```

The `100` ambiguous discovery items remain manual-review only; they did not meet target-discovery confidence/safety gates. No approval manifest was created.

Evidence:

- `out/reports/per-vault-index/broader-20260706T151108Z/REPORT.md`
- `out/reports/remaining-broader-triage-20260706T151405Z-source-protected/REPORT.md`
- `out/reports/remaining-broader-target-discovery-20260706T151405Z-source-protected/REPORT.md`

## Same-source vault exact-path rule — 2026-07-06

A later broader scan showed that most remaining `ambiguous_needs_operator_disambiguation` items were not semantic ambiguity; they were mirror ambiguity between `Memory-Vault/...` and `Soul-Vault/...` for an exact path-like wikilink from a `Memory-Vault` source.

Accepted rule:

```text
If source root is a non-protected vault root ending in `-Vault`,
and target is a path-like wikilink,
and the top candidate exactly equals `<source_root>/<target>.md`,
and that candidate has no safety flags,
then the item may become a proposal_candidate even if a protected mirror candidate is close in score.
```

This still does **not** authorize live apply. It only creates a proposal-ready batch for the normal gates: dry-run, readiness, explicit approval, backup, apply, post-verify. Protected source roots, including `Soul-Vault`, remain manual-only.

Latest evidence:

```text
proposal_candidates: 98
suppressed_by_policy: 5788
manual_review_required: 2
dry-run first25: passed
readiness first25 grouped: ready
live_mutation_authorized: false
apply_authority: none
```

Evidence:

The first pilot is grouped into one file-level target to avoid repeated `base_sha256` conflicts during live apply.

- `out/reports/remaining-broader-target-discovery-20260706T152315Z-same-vault-rule/REPORT.md`
- `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/proposal-first25.grouped.json`
- `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/dry-run-first25.grouped.json`
- `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/readiness-first25-grouped/REPORT.md`

## Live apply — same-source vault first25 pilot — 2026-07-06

After explicit operator confirmation, the first grouped same-source-vault pilot was applied to one live Memory-Vault file.

```text
status: applied + post-verify passed
target: /home/hermesadmin/Obsidian/Memory-Vault/00 Memory Graph Index.md
logical_replacements: 25
old_links_remaining_total: 0
new_links_present_total: 25
backup: /home/hermesadmin/Obsidian/_Backups/obsidian-operating-layer/20260706T153858Z-same-vault-rule-first25/00 Memory Graph Index.md
```

Evidence:

- `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/LIVE_APPLY_REPORT.first25.grouped.json`
- `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/POST_VERIFY.first25.grouped.json`
- `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/POST_VERIFY.first25.grouped.md`
- `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/LIVE_APPLY_DIFF.first25.grouped.patch`

Boundary: this was a single approved pilot batch, not standing authorization for unattended live apply.
