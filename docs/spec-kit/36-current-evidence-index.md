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
