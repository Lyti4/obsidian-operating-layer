# 36 — Current Evidence Index

Status: active evidence index
Date: 2026-07-05
Scope: tracked source index for current proposal-only/operator evidence pointers that would otherwise bloat acceptance or backlog docs.

## Purpose

Keep `docs/acceptance/index.md` and `docs/spec-kit/24-orchestration-backlog.md` concise while preserving reviewable pointers to the current generated reports/proposals under `out/`.

This document is an index only. It does not promote generated artifacts to source-of-truth status and does not authorize live mutation.

## Control-plane source surfaces

- First-read orchestrator spec: `docs/spec-kit/30-orchestrator-operating-spec.md`
- Operator flow / review queue: `docs/spec-kit/31-operator-flow-and-review-queue.md`
- Codex ⇄ Hermes channel: `docs/spec-kit/32-codex-hermes-communication-channel.md`, `tools/codex_hermes_comm.py`, `~/.codex-hermes/docs/ROLE_POLICY.json`
- Codex native runtime: `docs/spec-kit/33-codex-native-runtime.md`, `tools/hermes_codex_run.py`
- Agentic improvement loop: `docs/spec-kit/34-agentic-improvement-loop.md`
- Agentic OS control plane map: `docs/spec-kit/35-agentic-os-control-plane-map.md`
- Semantic workflow: `docs/spec-kit/29-semantic-proposal-workflow.md`
- Proposal routing contract: `src/obslayer/proposal_routing_contract_v1.py`, `tests/test_proposal_routing_contract_v1.py`
- Channel registry: `docs/spec-kit/29-channel-registry.md`, `docs/spec-kit/channel-registry.json`

## Current generated evidence pointers

These paths are generated artifacts and stay ignored by git unless a future review explicitly promotes a distilled source document.

- Broader Obsidian index / remaining-link triage / target discovery: `out/reports/per-vault-index/broader-20260706T151108Z/REPORT.md`, `out/reports/remaining-broader-triage-20260706T151405Z-source-protected/REPORT.md`, `out/reports/remaining-broader-target-discovery-20260706T151405Z-source-protected/REPORT.md`

- Semantic query report: `out/proposals/semantic-query-reports/final468-operator-review-20260704T093433Z/REPORT.md`
- Candidate decision packet: `out/proposals/semantic-candidate-decisions/final468-operator-review-20260704T105830Z/REPORT.md`
- Targeted semantic proposal: `out/proposals/semantic-targeted-proposals/link-hygiene-20260704T112830Z/REPORT.md`
- Semantic review index: `out/proposals/semantic-review-indexes/link-hygiene-20260704T1200Z/REPORT.md`
- Semantic indexing manifest: `out/reports/semantic-manifests/manual/REPORT.md`
- Operator decision packet: `out/proposals/operator-decision-packets/link-hygiene-20260704T153221Z/REPORT.md`
- Link hygiene evidence brief: `out/proposals/link-hygiene-evidence-briefs/20260704T154000Z/REPORT.md`
- Non-report working-note wikilink triage: `out/proposals/non-report-working-note-wikilink-triage/20260704T154634Z/REPORT.md`
- Working-note link targeted proposal: `out/proposals/working-note-link-targeted-proposals/20260704T155803Z/REPORT.md`
- Working-note link operator review: `out/proposals/working-note-link-operator-reviews/20260704T161938Z/REPORT.md`
- Working-note link manifest-candidate dry-run: `out/proposals/working-note-link-manifest-candidates/20260704T162439Z/REPORT.md`
- Working-note link live apply: `out/reports/working-note-link-apply/20260704T163336Z/REPORT.md`
- Working-note link post-apply verification: `out/reports/working-note-link-post-apply-verify/20260704T163336Z/REPORT.md`
- Working-note link post-apply observation: `out/reports/working-note-link-post-apply-observation/20260704T164100Z/REPORT.md`
- Held Reports README link apply: `out/reports/working-note-held-report-readme-apply/20260704T165519Z/REPORT.md`
- Post-held working-note wikilink triage: `out/reports/non-report-working-note-wikilink-post-held-triage/20260704T170534Z/REPORT.md`
- Next safe working-note disambiguation proposal: `out/proposals/working-note-link-next-safe-disambiguation/20260704T170712Z/REPORT.md`
- Current link hygiene read-only scan: `out/reports/link-hygiene-current-scan/20260704T-current-brief/REPORT.md`
- Latest accepted Nanobot scout sample: `out/reports/nanobot-cron-scout/20260704T152408Z/REPORT.md`
- Nanobot all-reports aggregate: `out/reports/nanobot-all-reports-aggregate-20260705.md`

- Remaining link target discovery: `out/reports/remaining-link-target-discovery-20260706T1500Z/REPORT.md` — repo-only target-discovery packet over 92 triaged leftovers; `proposal_candidates: 0`, `apply_authority: none`, no live mutation.
- Candidate-volume operator packet: `out/reports/candidate-volume-operator-packet/full-vault-proposal-only-20260706T182612Z/REPORT.md` — repo-only summary of full-vault proposal-only candidate volume, protected buckets, verify state, and unified-index readiness; `apply_authority: none`, no approval manifest.
- Manifest-candidate selector smoke: `out/reports/manifest-candidate-selector/grouped-next5-smoke/REPORT.md` and `out/reports/manifest-candidate-selector/grouped-next5-smoke/HERMES_ACCEPTANCE.md` — repo-only selector over existing operator-review evidence; `selected_count: 5`; inert authority preserved; full `make verify` passed; independent read-only review pending.

## Safety boundary

- Proposal-only/read-only unless a separate approval manifest says otherwise.
- `live_mutation_authorized: false` for this index.
- No approval manifest is created by this index.
- Do not edit live vaults, services, auth/profile state, cron, network exposure, or public/p paid surfaces from these pointers.


## 2026-07-05 full-vault automation roadmap fixation

| Artifact | Path | Role | Boundary |
|---|---|---|---|
| Full vault index | `out/reports/full-vault-index-analysis/20260705T084734Z/` | Current indexing stop point: 1121 markdown files, 12979 wikilinks, 7434 broken, 4052 ambiguous | read-only, no live mutation |
| Research synthesis | `out/reports/vault-automation-research/20260705T090600Z/` | Internet + Codex + Nanobot + delegation input for future automation architecture | research/report only |
| Document audit | `out/reports/document-audit/20260705T122800Z/` | Audit of project docs and generated evidence pointers before roadmap fixation | repo/docs only |
| Roadmap spec | `docs/spec-kit/37-vault-automation-indexing-roadmap.md` | Canonical continuation roadmap from the current indexing point | spec only; no apply authorization |

| Nanobot follow-up attempt | `out/reports/nanobot-roadmap-review-attempt/20260705T123300Z/` | Tried fresh Nanobot review via sanitized workspace packet; blocked by provider quota | no mutation; pending rerun |
| Nanobot-style delegated audit | async delegation `deleg_3248b6f9` | Independent Nanobot-style audit confirmed the roadmap direction: lane schema → scorer → archive-shadow resolver → decision ledger, with archive evidence-only and no live mutation without approval | no mutation; incorporated as confirmation |

Next accepted build direction: `lane-schema-v1`, `archive-shadow-index`, and `candidate-scorer-v1`, all repo-only and `live_mutation_authorized: false`.


## 2026-07-05 latest artifact delta

This section records the newest Obsidian automation surfaces flagged by Nanobot scout `out/reports/nanobot-cron-scout/20260705T135918Z/REPORT.md` so the generated evidence layer stays discoverable without promoting `out/` to source of truth.

| Slice / artifact | Source paths | Evidence paths | Boundary |
|---|---|---|---|
| Lane schema v1 | `src/obslayer/lane_schema_v1.py`, `tools/obsidian_lane_schema_v1.py`, `tests/test_lane_schema_v1.py` | `out/reports/lane-schema-v1/` | repo-only schema/reporting |
| Archive shadow index | `src/obslayer/archive_shadow_index.py`, `tests/test_archive_shadow_index.py` | `out/reports/archive-shadow-index/` | read-only classification; no mutation |
| Candidate scorer v1 | `src/obslayer/candidate_scorer_v1.py`, `tests/test_candidate_scorer_v1.py` | `out/reports/candidate-scorer-v1/` | evidence scoring only |
| Operator decision ledger v1 | `src/obslayer/operator_decision_ledger_v1.py`, `tests/test_operator_decision_ledger_v1.py` | `out/reports/operator-decision-ledger-v1/` | weak evidence/prior only; not authority |
| Proposal routing contract v1 | `src/obslayer/proposal_routing_contract_v1.py`, `tests/test_proposal_routing_contract_v1.py` | `out/reports/proposal-routing-contract-v1/` | routing-only; suggest/auto-propose/needs-human-review/blocked-refuse, no apply authority |
| Safe auto-proposal thresholds | `src/obslayer/safe_auto_proposal_thresholds.py`, `tools/obsidian_safe_auto_proposal_thresholds.py`, `tests/test_safe_auto_proposal_thresholds.py` | `out/reports/safe-auto-proposal-thresholds/` | dry-run/evidence-only; `live_mutation_authorized: false` |
| External tool benchmark | `src/obslayer/external_tool_benchmark.py`, `tools/obsidian_external_tool_benchmark.py`, `tests/test_external_tool_benchmark.py` | `out/reports/external-tool-benchmark/` | deterministic read-only comparison of external-tool patterns/signals; write-capable tools not run against the live vault |
| R7 narrow approved apply pilot | `tools/obsidian_apply.py`, approval manifest under proposal packet | `out/proposals/working-note-link-archive-duplicate-live-apply/20260705T083603Z/APPLY_REPORT.md` | user-approved live apply; 43 target files, 240 replacements, backups and post-verify recorded |
| Unified queue/state/decision surface v1 | `docs/spec-kit/31-operator-flow-and-review-queue.md`, `docs/spec-kit/37-vault-automation-indexing-roadmap.md` | `out/reports/unified-queue-state-decision-surface-v1/` | proposal-only contract boundary; no live mutation authorization |
| Latest docs-lag audit | `out/reports/nanobot-cron-scout/20260705T143118Z/REPORT.md`, `out/reports/nanobot-cron-scout/20260705T143118Z/docs-lag-audit/REPORT.md` | evidence for the current delta scan | read-only audit evidence; no live mutation |

R7 is not a blanket apply authorization. Future live apply packets still require their own approval manifest, backup plan, hash/old-text checks, post-verify, and rollback evidence. If a manifest needs changes after review, create a revised manifest packet rather than silently mutating the historical audit artifact after apply.


## 2026-07-05 Nanobot recommendation decision register

This section records Hermes acceptance decisions for recent Nanobot scout recommendations so recurring reports become an auditable decision input rather than an untracked chat-only signal. It does not authorize live mutation.

## Accepted current slices / canonical source pointers

These are the concise source-controlled pointers for the current accepted slices. They keep `out/` as evidence only and avoid promoting generated artifacts into source of truth.

| Slice | Canonical source pointer | Evidence pointer | Boundary |
|---|---|---|---|
| Generated-artifacts registry index | `docs/spec-kit/36-current-evidence-index.md` | current report/proposal pointers under `out/` | read-only index; no live mutation authorization |
| Unified queue/state/decision surface v1 | `docs/spec-kit/31-operator-flow-and-review-queue.md`, `docs/spec-kit/37-vault-automation-indexing-roadmap.md`, `docs/spec-kit/38-unified-queue-state-decision-surface-v1.md` | `out/reports/unified-queue-state-decision-surface-v1/` | proposal-only boundary; `live_mutation_authorized: false` |
| Roadmap continuation from full-vault fixation | `docs/spec-kit/37-vault-automation-indexing-roadmap.md` | `out/reports/full-vault-index-analysis/20260705T084734Z/` | repo-only continuation roadmap; no apply authorization |
| Nanobot scout / docs-lag evidence | `AGENTS.md`, `docs/orchestration-board.md` | `out/reports/nanobot-cron-scout/` | advisory read-only evidence; Hermes-accepted decisions only |

| Nanobot recommendation | Decision | Accepted boundary / next gate | Evidence |
|---|---|---|---|
| Add a canonical generated artifacts index / registry for latest proposals and reports | Accepted, partial | Maintain this source index as the canonical concise pointer surface; keep generated `out/` artifacts as evidence, not source of truth. Next gate: close remaining drift by adding only distilled entries. | `out/reports/nanobot-cron-scout/20260705T162320Z/REPORT.md`, this document |
| Unify queue state, lane schema, proposal routing, operator decision ledger, thresholds, and candidate scoring | Accepted | Track as `unified-queue-state-decision-surface-v1`; proposal-only and `live_mutation_authorized: false`. | `docs/spec-kit/38-unified-queue-state-decision-surface-v1.md`, `out/reports/unified-queue-state-decision-surface-v1/20260705T000000Z/REPORT.md` |
| Introduce candidate scoring + thresholding over semantic proposals, external-tool findings, and archive-shadow signals | Accepted as read-only/proposal-only, not autonomous authority | Scoring may rank and explain review candidates; it must not approve manifests, mutate the vault, or bypass Hermes acceptance. | `src/obslayer/candidate_scorer_v1.py`, `src/obslayer/safe_auto_proposal_thresholds.py`, tests |
| Use Nanobot as an architecture/docs-lag scout | Accepted with supervision | Nanobot may observe and recommend through read-only reports; Hermes remains acceptance owner and records accept/defer/reject decisions here. | `AGENTS.md`, `out/reports/nanobot-cron-scout/` |
| Create an acceptance-gate synthesizer / dashboard | Deferred | Revisit after fixture-level fail-closed contracts and the generated-artifacts index are stable. | `docs/orchestration-board.md` |
| Allow Nanobot/automation to perform live apply, cron/auth/service changes, deploys, or network exposure | Rejected for current scope | Requires separate explicit Dmitry approval and the normal backup/apply/verify/rollback evidence chain; no standing authorization. | `AGENTS.md`, `docs/acceptance/index.md` |

### Verification evidence

Commands run for this docs update:

- `python3 -m pytest -q tests/test_external_tool_benchmark.py tests/test_safe_auto_proposal_thresholds.py tests/test_operator_decision_ledger_v1.py tests/test_lane_schema_v1.py tests/test_archive_shadow_index.py tests/test_candidate_scorer_v1.py`
- `git diff --check`
- `python3 -m compileall -q src tools`
- `git status --short`

Final fan-in report: `out/reports/latest-artifacts-delta/final-board-report.md`.

## 2026-07-06 remaining-link suppression gate acceptance

This section closes the docs/index lag flagged by Nanobot scout `out/reports/nanobot-cron-scout/20260706T142630Z/REPORT.md`. It records the accepted source pointers for the current remaining-link triage/suppression surface without promoting generated `out/` artifacts to source-of-truth status.

| Slice | Canonical source pointer | Evidence pointer | Boundary |
|---|---|---|---|
| Generated report noise policy | `docs/spec-kit/38-generated-report-noise-policy.md` | selector/policy tests and current policy artifact | generated/audit/report links are historical evidence unless separately approved |
| Protected cross-vault link policy | `docs/spec-kit/39-protected-cross-vault-link-policy.md` | `tests/test_remaining_link_triage.py` | Soul/cross-vault links stay manual/protected |
| Indexing manifest / doctor contract | `docs/spec-kit/40-indexing-manifest-and-doctor-contract.md` | `tests/test_indexing_manifest_doctor.py` | repo-only validation; no live mutation |
| Acceptance bundle doctor | `docs/spec-kit/41-acceptance-bundle-doctor.md` | `tests/test_acceptance_bundle_doctor.py` | bundle completeness audit only |
| Operator review packet | `docs/spec-kit/42-operator-review-packet.md` | `tests/test_operator_review_packet.py` | proposal-only packet, no apply authority |
| Manual review selector pipeline | `docs/spec-kit/43-manual-review-selector-pipeline.md` | `out/reports/manual-review-selector-suppression-gate-smoke-20260706T1420Z/` | selector/review only; `live_mutation_authorized: false` |
| External autograph policy adapter | `docs/spec-kit/44-external-autograph-policy-adapter.md`, `src/obslayer/policies/external_autograph_policy.v1.json` | schema validation and selector tests | repo-derived filters only; no live vault mutation |
| Remaining link suppression gate | `docs/spec-kit/45-remaining-link-suppression-gate.md` | `out/reports/remaining-link-suppression-gate-20260706T1420Z/HERMES_ACCEPTANCE_REPORT.md`, `out/reports/remaining-link-suppression-gate-20260706T1420Z/CODEX_FORCE_REVIEW.md` | suppresses only already-triaged `apply_authority: none` links; no approval manifest, no apply |

Safety invariant for this accepted slice:

```text
live_mutation_authorized: false
approval_manifest_created: false
apply_authority: none
```

Codex force review found and fixed one fail-closed hardening issue: string `"true"` in `live_mutation_authorized` is now treated as true-like and refused by the suppression index.


## 2026-07-06 same-source vault target-discovery rule

The broader remaining-link discovery layer now promotes non-protected same-source-vault exact path matches to proposal-only candidates when the competing ambiguity is a protected mirror candidate. This converts 98 previously manual `Memory-Vault` ambiguity items into proposal candidates while preserving fail-closed behavior for protected roots and generated/report surfaces.

| Artifact | Path | Result |
|---|---|---|
| Target discovery report | `out/reports/remaining-broader-target-discovery-20260706T152315Z-same-vault-rule/REPORT.md` | `proposal_candidates: 98`, `manual_review_required: 2`, `suppressed_by_policy: 5788` |
| First pilot proposal | `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/proposal-first25.grouped.json` | 25 logical replacements grouped into 1 file-level target |
| Dry-run | `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/dry-run-first25.grouped.json` | passed; no live write |
| Readiness | `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/readiness-first25-grouped/REPORT.md` | ready for human-approved apply; still `apply_authority: none` |

Safety boundary: no live vault mutation was performed in this slice.

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

## 2026-07-06 same-vault live pilot and board registry refresh

- Same-vault remaining-link rule pilot: `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/HERMES_ACCEPTANCE_REPORT.md` — proposal/readiness evidence for the first grouped 25-change pilot.
- Same-vault first live apply post-verify: `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/POST_VERIFY.first25.grouped.json` — `status: passed`, `logical_replacements: 25`, `old_links_remaining_total: 0`, `new_links_present_total: 25`.
- Same-vault first live apply diff: `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/LIVE_APPLY_DIFF.first25.grouped.patch` — generated evidence only; not source truth.
- Latest Nanobot audit scout: `out/reports/nanobot-cron-scout/20260706T172004Z/REPORT.md` — advisory verdict `lagging`; no mutation authority.
- Generated-artifacts registry drift handoff: `out/reports/kanban-triage-continuation/20260706T173514Z-generated-artifacts-registry-drift/REPORT.md` — docs-update slice evidence for board card `t_423691d1`.

Safety: these are evidence pointers only. They do not authorize unattended live apply, do not create an approval manifest, and do not promote generated artifacts into git-tracked source truth.

## 2026-07-06 same-vault next5 proposal-readiness

- Same-vault next5 proposal report: `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/NEXT5_PROPOSAL_REPORT.md` — proposal-only/readiness-only batch after the first live pilot; 5 logical replacements remain present in `Memory-Vault/00 Memory Graph Index.md`.
- Same-vault next5 grouped proposal: `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/proposal-next5.grouped.json`.
- Same-vault next5 dry-run/readiness evidence: `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/dry-run-next5.grouped.json`, `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/readiness-next5-grouped/approved-apply-readiness-v1.json`.

Safety: no live apply was run for this next5 batch. The readiness manifest is not standing authorization; explicit chat approval, backup, apply, and post-verify are still required.

## 2026-07-06 same-vault next5 live apply

```text
status: passed
target: /home/hermesadmin/Obsidian/Memory-Vault/00 Memory Graph Index.md
logical_replacements: 5
old_links_remaining_total: 0
new_links_present_total: 5
backup: /home/hermesadmin/Obsidian/_Backups/obsidian-operating-layer/20260706-174737Z/00 Memory Graph Index.md
```

Evidence:

- `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/LIVE_APPLY_REPORT.next5.grouped.json`
- `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/POST_VERIFY.next5.grouped.json`
- `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/POST_VERIFY.next5.grouped.md`
- `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/LIVE_APPLY_DIFF.next5.grouped.patch`

Boundary: this was Dmitry-approved exact `next5` batch, not standing authorization for unattended live apply.

## 2026-07-06 operator review packet grouped-proposal support

The operator review packet can now consume grouped same-vault proposal evidence (`targets[].evidence.grouped_replacements[]`) and render a repo-only human review packet before any approval manifest exists. Grouped target paths and `vault_root` remain context only; output safety keeps `target_paths: []`, `apply_authority: none`, `approval_manifest_created: false`, and `live_mutation_authorized: false`.

Evidence:

- Spec: `docs/spec-kit/42-operator-review-packet.md`
- Implementation: `src/obslayer/operator_review_packet.py`
- Tests: `tests/test_operator_review_packet.py`
- Smoke packet: `out/reports/operator-review-packet/grouped-next5-smoke/operator-review-packet.json`
- Smoke report: `out/reports/operator-review-packet/grouped-next5-smoke/REPORT.md`

Verification:

```text
python3 -m pytest -q tests/test_operator_review_packet.py tests/test_remaining_link_target_discovery.py -> 15 passed
python3 tools/obsidian_operator_review_packet.py --repo . --proposal-packet out/proposals/remaining-link-same-vault-rule/20260706T152315Z/proposal-next5.grouped.json --out-dir out/reports/operator-review-packet/grouped-next5-smoke -> ready_for_human_review, 5 items
git diff --check -> passed
```

Safety: this is review-only/proposal-only evidence. It does not authorize live apply and does not create an approval manifest.

## 2026-07-06 unified operator review index

- Slice: `unified-operator-review-index-v1`
- Spec: `docs/spec-kit/47-unified-operator-review-index.md`
- Implementation: `src/obslayer/unified_operator_review_index.py`
- CLI: `tools/obsidian_unified_operator_review_index.py`
- Tests: `tests/test_unified_operator_review_index.py`
- Smoke evidence: `out/reports/unified-operator-review-index/hermes-smoke/REPORT.md`

Boundary: repo-only pre-full-vault-indexing control panel. It aggregates pointers/status from `out/` and docs only, keeps fixed inert safety, and does not create approval manifests or grant apply authority.
## 2026-07-06 full-vault proposal-only unified gate

- Run: `out/live-proposal-only-20260706T182612Z/`
- Unified index: `out/reports/unified-operator-review-index/full-vault-proposal-only-20260706T182612Z/REPORT.md`
- Boundary: read-only observe of `/home/hermesadmin/Obsidian`, proposal-only output under repo `out/`, no approval manifest, no live apply.
- Result: `ready_for_operator_review`; regenerated unified index now includes the candidate-volume packet and removes the stale missing JSON pointer: 14 artifacts, 14 present, 0 missing, 0 blocked, 11 proposal-only pointers, 2 ready/review JSON packets.
- Safety: fixed `apply_authority: none`, `target_paths: []`, `live_mutation_authorized: false`, `approval_manifest_created: false`, `approval_manifest_authority: false`.

## 2026-07-06 candidate-volume operator packet

- Spec: `docs/spec-kit/48-candidate-volume-operator-packet.md`
- Implementation: `src/obslayer/candidate_volume_operator_packet.py`
- CLI: `tools/obsidian_candidate_volume_operator_packet.py`
- Tests: `tests/test_candidate_volume_operator_packet.py`
- Evidence: `out/reports/candidate-volume-operator-packet/full-vault-proposal-only-20260706T182612Z/REPORT.md`
- Unified pointer: `out/reports/unified-operator-review-index/full-vault-proposal-only-20260706T182612Z/REPORT.md`

Result: `ready_for_operator_review`; protected hits `447`; proposal targets `0`; `first_manifest_candidate_queue: []`; fixed inert safety at nested and root levels. Boundary: repo-local evidence only; no approval manifest, no target authorization, no live apply.
## 2026-07-06 Manifest-Candidate Selector

- Spec: `docs/spec-kit/49-manifest-candidate-selector.md`
- Implementation: `src/obslayer/manifest_candidate_selector.py`
- CLI: `tools/obsidian_manifest_candidate_selector.py`
- Tests: `tests/test_manifest_candidate_selector.py`
- Smoke evidence: `out/reports/manifest-candidate-selector/grouped-next5-smoke/REPORT.md`

The selector uses only existing repo-local JSON artifacts, selected 5 grouped-next5 candidates, and remains evidence-only/proposal-only. It does not create an approval manifest and keeps `apply_authority: none`.

## 2026-07-06 control-plane reconciliation

Current packet/index/doctor family is consolidated as repo-only control-plane evidence:

- doctor gates: semantic manifest doctor, indexing manifest doctor, acceptance bundle doctor;
- policy/suppression gates: generated report noise, protected cross-vault policy, external autograph policy adapter, remaining-link suppression;
- discovery/scoring gates: remaining-link target discovery, archive shadow index, candidate scorer, safe auto-proposal thresholds;
- operator packet gates: operator review packet, unified operator review index, candidate-volume operator packet;
- selector gates: manual review selector and manifest-candidate selector.

Current boundary: all current gates preserve `live_mutation_authorized: false`, `approval_manifest_created: false`, `apply_authority: none`, and empty `target_paths` unless a separate Dmitry-approved live manifest is created for an exact proposal.

Pending before any next live pilot:

1. independent read-only review of `manifest-candidate-selector-v1` against the current grouped-next5 smoke evidence;
2. refreshed unified review index after any artifact pointer changes;
3. exact approval manifest, backup, apply, and post-verify only if Dmitry explicitly approves a narrow proposal.
