# Acceptance Index — Obsidian Operating Layer

Status: current acceptance map  
Scope: source-of-truth summary for accepted, limited, and not-yet-accepted project capabilities.

## Accepted now

| Layer | Status | Evidence / source |
|---|---|---|
| Safety core | Accepted baseline | `docs/spec-kit/03-safety-contract.md`, tests, `make verify` |
| Observe/propose/verify/apply-dry-run | Accepted baseline | `README.md`, `docs/spec-kit/14-operational-acceptance-report.md` |
| Approval manifest binding | Accepted baseline | tests + apply policy in `AGENTS.md` |
| Protected path refusal | Accepted baseline | tests + safety contract |
| Review dashboard list/explain | Accepted baseline | `docs/obsidian-review-dashboard/index.md`, acceptance reports |
| Sandbox vault copies | Accepted baseline | `tools/obsidian_sandbox.py`, E2E evidence |
| Diagram/PDF report generation | Accepted with manual readability gate | `docs/spec-kit/15-manual-and-adapter-acceptance.md` |
| Controlled autonomy queue | Accepted only as explicit manual jobs | `docs/controlled-autonomy.md`; no scheduler installed |
| Indexing wrapper/runtime | Accepted for sandbox, guarded read-only probes, and final468 Graphify-derived semantic query smoke | `docs/spec-kit/20-indexing-runtime-acceptance.md`, `out/reports/graphify-final468-acceptance-20260704T065729Z/REPORT.md` |
| Semantic query proposal-only reports | Accepted as review-candidate path with empty `targets`, candidate notes, safety boundary, and no apply authorization | `tools/obsidian_semantic_proposal_report.py`, `tools/obsidian_review_dashboard.py explain`, `out/proposals/semantic-query-reports/final468-operator-review-20260704T093433Z/REPORT.md`, `EXPLANATION.md` |
| Semantic targeted proposal/review index | Accepted as proposal-only operator review path; candidate paths are evidence inputs, not edit targets | `tools/obsidian_semantic_targeted_proposal.py`, `tools/obsidian_semantic_review_index.py`, `docs/spec-kit/29-semantic-proposal-workflow.md` |
| Semantic indexing manifest | Accepted as the terminal proposal-only index over generated Graphify/embedding/query/proposal/review artifacts; validates empty targets and no live mutation authorization | `tools/obsidian_semantic_manifest.py`, `src/obslayer/semantic_manifest.py`, `docs/spec-kit/29-semantic-proposal-workflow.md` |
| Proposal routing contract v1 | Accepted as routing-only classifier for `suggest` / `auto-propose` / `needs-human-review` / `blocked/refuse`; decision ledger remains weak evidence only and does not grant apply authority | `src/obslayer/proposal_routing_contract_v1.py`, `tests/test_proposal_routing_contract_v1.py`, `docs/spec-kit/31-operator-flow-and-review-queue.md`, `docs/spec-kit/37-vault-automation-indexing-roadmap.md` |
| Unified queue/state/decision surface v1 | Proposal-only boundary under design; unifies queue state, lane schema, scorer, ledger, thresholds, and routing, but preserves `live_mutation_authorized: false` | `docs/spec-kit/31-operator-flow-and-review-queue.md`, `docs/spec-kit/37-vault-automation-indexing-roadmap.md`, `docs/spec-kit/36-current-evidence-index.md` |
| Lane schema v1 | Accepted as repo-only/operator packet layer for current full-vault lanes; includes lane summaries and safety fields, creates no approval manifest, no targets, and no live mutation authorization | `src/obslayer/lane_schema_v1.py`, `tools/obsidian_lane_schema_v1.py`, `tests/test_lane_schema_v1.py`, `out/reports/lane-schema-v1/20260705T171353Z/REPORT.md`, `docs/spec-kit/37-vault-automation-indexing-roadmap.md` |
| Archive shadow index v1 | Accepted as evidence-only/proposal-only archive, backup, duplicate, and redirect shadow classifier; creates no approval manifest, no targets, and no live mutation authorization | `src/obslayer/archive_shadow_index.py`, `tools/obsidian_archive_shadow_index.py`, `tests/test_archive_shadow_index.py`, `out/reports/archive-shadow-index/20260705T173124Z/REPORT.md`, `docs/spec-kit/37-vault-automation-indexing-roadmap.md` |
| Candidate scorer v1 | Accepted as repo-only/evidence-only candidate packet and CLI writer; records reason codes, feature breakdowns, top-two gaps, and hard-stop/review gates; creates no approval manifest, no targets, no apply authority, and no live mutation authorization | `src/obslayer/candidate_scorer_v1.py`, `tools/obsidian_candidate_scorer.py`, `tests/test_candidate_scorer_v1.py`, `out/reports/candidate-scorer-v1/20260705T175815Z/REPORT.md`, `docs/spec-kit/37-vault-automation-indexing-roadmap.md` |
| Operator decision ledger v1 | Accepted as repo-only/evidence-only append-only decision ledger; records source pattern, proposed target, decision, reason, scorer version, verification outcome, and inert evidence refs; creates no approval manifest, no targets, and no live mutation authorization | `src/obslayer/operator_decision_ledger_v1.py`, `tools/obsidian_operator_decision_ledger.py`, `tests/test_operator_decision_ledger_v1.py`, `out/reports/operator-decision-ledger-v1/20260705T180705Z/REPORT.md`, `docs/spec-kit/37-vault-automation-indexing-roadmap.md` |
| Safe auto proposal thresholds v1 | Accepted as repo-only/evidence-only dry-run proposal threshold packet and CLI writer; consumes candidate-scorer-v1 packets and emits dry-run proposals only for deterministic-high, non-sensitive, non-archive-collision candidates; creates no approval manifest, no targets, no apply authority, and no live mutation authorization | `src/obslayer/safe_auto_proposal_thresholds_v1.py`, `tools/obsidian_safe_auto_proposal_thresholds.py`, `tests/test_safe_auto_proposal_thresholds_v1.py`, `out/reports/safe-auto-proposal-thresholds-v1/20260705T181910Z/REPORT.md`, `docs/spec-kit/37-vault-automation-indexing-roadmap.md` |
| External tool benchmark v1 | Accepted as repo-only/evidence-only deterministic read-only simulation/comparison; consumes current candidate-scorer-v1 packet shapes, does not execute external tool subprocesses/APIs/write modes, and converts differences into scorer test cases/proposal-only records; creates no approval manifest, no targets, and no live mutation authorization | `src/obslayer/external_tool_benchmark.py`, `tools/obsidian_external_tool_benchmark.py`, `tests/test_external_tool_benchmark.py`, `out/reports/external-tool-benchmark/20260705T183948Z/REPORT.md`, `docs/spec-kit/37-vault-automation-indexing-roadmap.md` |
| Orchestrator operating spec | Accepted as first-read operator consolidation; does not replace source specs or authorize live apply | `docs/spec-kit/30-orchestrator-operating-spec.md`, `docs/spec-kit/00-overview.md`, `docs/spec-kit/24-orchestration-backlog.md` |
| Operator flow / review queue | Accepted as proposal-only coordination contract; queue states do not authorize live apply | `docs/spec-kit/31-operator-flow-and-review-queue.md`, `tools/obsidian_operator_review_queue.py`, `docs/spec-kit/30-orchestrator-operating-spec.md` |
| Codex ⇄ Hermes communication channel | Accepted as local task/report/ACK protocol with explicit rights; no cron installed by default; Hermes verifies Codex outputs | `docs/spec-kit/32-codex-hermes-communication-channel.md`, `tools/codex_hermes_comm.py`, `~/.codex-hermes/docs/ROLE_POLICY.json` |
| Agentic improvement loop | Accepted as proposal-first operating contract: Nanobot scouts, Hermes triages/specs/queues, Codex reviews or implements bounded repo tasks, Hermes verifies | `docs/spec-kit/34-agentic-improvement-loop.md`, `~/.codex-hermes/comm/hermes-inbox/agentic-os-project-wide-review-20260704.wrapper-20260704T193616Z.report.json` |
| Agentic OS control plane map | Accepted as canonical operator index for orchestrator/review-queue/Codex-Hermes/runtime/acceptance/docs-lag surfaces; documentation only, no live apply authorization | `docs/spec-kit/35-agentic-os-control-plane-map.md`, `docs/spec-kit/00-overview.md`, `src/obslayer/project_docs_lag_audit.py` |
| Approved apply readiness v1 | Accepted as repo-only/evidence-only readiness checker for proposal/approval-manifest bundles; validates proposal-manifest alignment, protected target refusal, hash binding, evidence refs, backup-root policy, and post-verify requirement; creates no approval manifest, no targets, no apply authority, and no live mutation authorization | `src/obslayer/approved_apply_readiness_v1.py`, `tools/obsidian_approved_apply_readiness.py`, `tests/test_approved_apply_readiness_v1.py`, `out/reports/approved-apply-readiness-v1/20260705T185155Z/REPORT.md`, `docs/spec-kit/37-vault-automation-indexing-roadmap.md` |
| Generated report noise policy | Accepted as selector/policy boundary for generated, audit, evidence, and report surfaces; suppresses noise from apply queues without changing historical artifacts | `docs/spec-kit/38-generated-report-noise-policy.md`, `src/obslayer/policies/external_autograph_policy.v1.json`, `tests/test_manual_review_selector_v1.py` |
| Protected cross-vault link policy | Accepted as manual/protected boundary for Soul/cross-vault links; no automatic retarget/create/apply authority | `docs/spec-kit/39-protected-cross-vault-link-policy.md`, `src/obslayer/remaining_link_triage.py`, `tests/test_remaining_link_triage.py` |
| Indexing manifest / doctor contract | Accepted as repo-only validation contract for generated indexes and manifests; no live vault mutation | `docs/spec-kit/40-indexing-manifest-and-doctor-contract.md`, `src/obslayer/indexing_manifest_doctor.py`, `tools/obsidian_indexing_doctor.py`, `tests/test_indexing_manifest_doctor.py` |
| Acceptance bundle doctor | Accepted as repo-only audit helper for bundle completeness and safety flags; no approval authority | `docs/spec-kit/41-acceptance-bundle-doctor.md`, `src/obslayer/acceptance_bundle_doctor.py`, `tools/obsidian_acceptance_bundle_doctor.py`, `tests/test_acceptance_bundle_doctor.py` |
| Operator review packet | Accepted as proposal-only operator packet layer; collects review evidence and preserves `apply_authority: none` until separate approval | `docs/spec-kit/42-operator-review-packet.md`, `src/obslayer/operator_review_packet.py`, `tools/obsidian_operator_review_packet.py`, `tests/test_operator_review_packet.py` |
| Manual review selector pipeline | Accepted as policy-backed manual review selector; classifies safe candidates and forbidden/manual/generated surfaces without live mutation | `docs/spec-kit/43-manual-review-selector-pipeline.md`, `src/obslayer/manual_review_selector_v1.py`, `tools/obsidian_manual_review_selector.py`, `tests/test_manual_review_selector_v1.py` |
| External autograph policy adapter | Accepted as machine-readable policy adapter for repo-derived filters; feeds classifier/selector logic only and does not mutate the vault | `docs/spec-kit/44-external-autograph-policy-adapter.md`, `src/obslayer/external_autograph_policy.py`, `src/obslayer/policies/external_autograph_policy.v1.json`, `docs/spec-kit/schemas/external-autograph-policy.schema.json` |
| Remaining link suppression gate | Accepted as repo-only suppression gate for already-triaged broken/ambiguous links; hides known `apply_authority: none` buckets from future scorer/apply queues while preserving audit evidence | `docs/spec-kit/45-remaining-link-suppression-gate.md`, `src/obslayer/remaining_link_triage.py`, `src/obslayer/candidate_scorer_v1.py`, `out/reports/remaining-link-suppression-gate-20260706T1420Z/HERMES_ACCEPTANCE_REPORT.md`, `CODEX_FORCE_REVIEW.md` |
| Remaining link target discovery v1 | Accepted as repo-only/evidence-only discovery layer for triaged `broken`/`ambiguous` leftovers; current packet found zero proposal candidates and grants no apply authority | `src/obslayer/remaining_link_target_discovery.py`, `tools/obsidian_remaining_link_target_discovery.py`, `tests/test_remaining_link_target_discovery.py`, `docs/spec-kit/46-remaining-link-target-discovery.md`, `out/reports/remaining-link-target-discovery-20260706T1500Z/REPORT.md` |
| Unified operator review index v1 | Accepted as repo-only pre-full-vault-indexing control panel; aggregates `out/` and docs pointers only; fixed inert safety, no approval/apply authority | `src/obslayer/unified_operator_review_index.py`, `tools/obsidian_unified_operator_review_index.py`, `tests/test_unified_operator_review_index.py`, `docs/spec-kit/47-unified-operator-review-index.md`, `out/reports/unified-operator-review-index/hermes-smoke/REPORT.md` |
| Unified control-plane evidence index v1 | Accepted as repo-only evidence-to-decision landing page; canonical generated artifact is inert and points to current docs/evidence without granting apply authority | `docs/spec-kit/50-unified-control-plane-evidence-index.md`, `out/reports/unified-control-plane-index/hermes-verify/REPORT.md`, `out/reports/unified-control-plane-index/hermes-verify/control-plane-index.json` |
| Graphify incremental index wrapper | Accepted as repo-only/dry-run-first wrapper over existing Graphify handoff, delta embedding manifest selection, optional bounded embedding run, and optional query smoke; writes only under repo `out/`, creates no approval manifest, no targets, and no live mutation authority | `src/obslayer/graphify_incremental_index.py`, `tools/obsidian_graphify_incremental_index.py`, `tests/test_graphify_incremental_index.py` |
| Candidate-volume operator packet v1 | Accepted as repo-local operator gate over observe/propose/verify/unified evidence; reports candidate/protected volume and route buckets without selecting or authorizing targets | `docs/spec-kit/48-candidate-volume-operator-packet.md`, `src/obslayer/candidate_volume_operator_packet.py`, `tools/obsidian_candidate_volume_operator_packet.py`, `tests/test_candidate_volume_operator_packet.py`, `out/reports/candidate-volume-operator-packet/full-vault-proposal-only-20260706T182612Z/REPORT.md` |
| R13 standing-baseline reconciliation | Accepted docs/evidence alignment after standing baseline codification; records DB-as-state, docs-as-policy/mirror, out-as-evidence, and stale grouped-next5 boundary | `docs/spec-kit/36-current-evidence-index.md`, `docs/spec-kit/37-vault-automation-indexing-roadmap.md`, `docs/orchestration-board.md`, `docs/triage/kanban-board.md` |
| Standing link-prefix baseline v1 | Accepted as repo-only/read-only baseline for the standing deterministic `[[Hermes/...]]` → `[[Memory-Vault/Hermes/...]]` policy; reports current candidate counts and authority flags without creating manifests or mutating the live vault | `src/obslayer/standing_safe_link_prefix_policy.py`, `src/obslayer/standing_safe_link_prefix_baseline.py`, `tools/obsidian_standing_safe_link_prefix_baseline.py`, `tests/test_standing_safe_link_prefix_baseline.py`, `out/reports/standing-safe-link-prefix-baseline/live-current/REPORT.md` |
| Manifest-candidate selector v1 | Accepted as repo-only selector smoke over existing JSON evidence after independent read-only Codex review; selects at most five review candidates and keeps approval/apply authority empty. The `grouped-next5` smoke output is now historical/stale for new manifests and must not be reused without fresh current-input selector evidence | `docs/spec-kit/49-manifest-candidate-selector.md`, `src/obslayer/manifest_candidate_selector.py`, `tools/obsidian_manifest_candidate_selector.py`, `tests/test_manifest_candidate_selector.py`, `out/reports/manifest-candidate-selector/grouped-next5-smoke/HERMES_ACCEPTANCE.md`, Codex review `manifest-selector-independent-review-20260707T044711Z.codex_report.json` |
| R7 narrow approved apply pilot | Accepted for the single reviewed archive-duplicate wikilink packet only; not a standing live-apply authorization | `out/proposals/working-note-link-archive-duplicate-live-apply/20260705T083603Z/approval-manifest.json`, `APPLY_REPORT.md`, backup `/home/hermesadmin/Obsidian/_Backups/obsidian-operating-layer/20260705-083637Z` |

## Current packet/index/doctor taxonomy

| Family | Components | Role | Authority boundary |
|---|---|---|---|
| Doctor gates | Semantic manifest doctor, indexing manifest doctor, acceptance bundle doctor | Validate an existing manifest/bundle and fail closed on missing evidence, unsafe flags, or out-of-repo artifacts | Read-only validation only; no rebuild, no live vault scan, no approval manifest, no targets |
| Policy / suppression gates | Generated report noise policy, protected cross-vault policy, remaining-link suppression gate, external autograph policy adapter | Classify generated/protected/manual surfaces so they do not re-enter apply queues as false positives | May suppress or mark manual; may not rewrite notes or create targets |
| Discovery / scoring gates | Remaining-link target discovery, candidate scorer, archive shadow index, safe auto-proposal thresholds | Produce proposal-only candidate evidence and risk bands from existing indexes | Evidence-only; candidates are review inputs, not apply authority |
| Operator packet gates | Operator review packet, unified operator review index, candidate-volume operator packet | Give Hermes/Dmitry a compact review surface over repo-local `out/` and docs evidence | Fixed inert safety: `live_mutation_authorized: false`, `approval_manifest_created: false`, `apply_authority: none`, `target_paths: []` |
| Selector gates | Manual review selector, manifest-candidate selector | Narrow noisy evidence into a small review queue | Selects review candidates only; separate explicit approval manifest is still required for any live apply |

## Limited / conditional

| Capability | Current boundary | Next gate |
|---|---|---|
| External MCP/RAG adapters | Sandbox/read-only/proposal-only | adapter-specific sandbox scorecard |
| Semantic indexing | Accepted for final468 sandbox/derived-cache pass and proposal-only candidate reports; no live vault mutation; no unattended routine job | explicit approval for any live apply |
| Live vault proposal generation | Read-only observation + proposal bundle | human review of proposal and manifest |
| Live apply | Single R7 packet accepted/applied; not generally enabled | new explicit approval manifest, backup, apply, verify per future packet |
| Manifest-candidate selector | Repo-only selector smoke is Hermes-accepted, but it is not an apply gate | independent read-only review, then explicit approval manifest for any live pilot |

## Not accepted yet

- Unreviewed live vault mutation.
- Direct write/delete/move by external MCP/RAG/plugin tools.
- Scheduling/cron/systemd for controlled autonomy.
- Routine unattended production semantic indexing without explicit schedule/resource approval.
- Any handling that prints or stores secrets in notes/reports.

## Required evidence for future acceptance

For each new accepted capability, add:

1. command(s) run;
2. exact artifact paths;
3. pass/fail result;
4. safety boundary statement;
5. rollback/disable path;
6. whether the live vault was mutated.

## Current operator default

When uncertain, treat the system as:

```text
read-only live vault + sandbox writes + proposal-only live changes
```

Live apply remains opt-in per proposal.

## Current semantic/orchestrator evidence pointers

Current generated report/proposal pointers live in `docs/spec-kit/36-current-evidence-index.md` so this acceptance page stays concise. The index now also carries the accepted current-slice pointers for the registry drift fix, remains proposal-only/read-only, and does not authorize live mutation.

## Codex native runtime

Codex is made repo-native through `docs/spec-kit/33-codex-native-runtime.md`, `/home/hermesadmin/.codex-hermes/bin/hermes-codex-run`, schema-versioned task/report packets, and explicit separation from Nanobot's architecture scout channel. Nanobot may recommend Codex tasks; Hermes dispatches and accepts them.

## Latest broader-vault link hygiene evidence

- Remaining-link target discovery: Accepted as repo-only/proposal-only discovery; same-source-vault exact-path rule now finds 98 proposal candidates and a first 25-change pilot is dry-run/readiness-ready, but no live apply is authorized without explicit approval + backup + post-verify; evidence: `docs/spec-kit/46-remaining-link-target-discovery.md`, `out/reports/remaining-broader-target-discovery-20260706T152315Z-same-vault-rule/REPORT.md`, `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/readiness-first25-grouped/REPORT.md`
- Same-source-vault first25 live apply: Applied after explicit operator confirmation to `/home/hermesadmin/Obsidian/Memory-Vault/00 Memory Graph Index.md`; 25 logical replacements, post-verify passed, old links remaining 0; backup `/home/hermesadmin/Obsidian/_Backups/obsidian-operating-layer/20260706T153858Z-same-vault-rule-first25/00 Memory Graph Index.md`; evidence `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/POST_VERIFY.first25.grouped.md`. This is a single approved pilot, not standing authorization.
- Same-source-vault grouped next5 live apply: Reconciled as already applied+verified for the exact grouped `next5` batch; 5 logical replacements, post-verify passed, old links remaining 0, new links present 5; backup `/home/hermesadmin/Obsidian/_Backups/obsidian-operating-layer/20260706-174737Z/00 Memory Graph Index.md`; evidence `out/proposals/remaining-link-same-vault-rule/20260706T152315Z/POST_VERIFY.next5.grouped.md` and `out/reports/kanban-triage-continuation/20260707T034602Z-next5-manifest-reconciliation/HERMES_RECONCILIATION.md`. This is a single approved/reconciled batch, not standing authorization.
- Nanobot recommendation follow-up: Accepted as repo-only docs/index freshness work. Current labels remain: generated `out/` artifacts are evidence only, operator/proposal packets are proposal-only unless a fresh approval manifest exists, and live vault mutation remains opt-in per exact proposal.

## 2026-07-07 candidate scorer follow-up acceptance

The `remaining-link-scorer-improvement-v1` follow-up is accepted as repo-only hardening of the already accepted Candidate scorer v1 layer. It adjusts deterministic source-context weights and adds same-vault/archive-collision regression coverage.

Evidence:

- `src/obslayer/candidate_scorer_v1.py`
- `tests/test_candidate_scorer_v1.py`
- `out/reports/remaining-link-scorer-improvement-v1/final-report/REPORT.md`

Boundary: scorer/proposal evidence only; no approval manifest, no target paths, no live mutation authority.

## 2026-07-07 fresh selector v3 acceptance note

`remaining-link-fresh-selector-v3` is accepted as fresh repo-only selector evidence after scorer hardening.

Evidence:

- `out/reports/remaining-link-fresh-selector-v3/20260707T123534Z/REPORT.md`
- `out/reports/remaining-link-fresh-selector-v3/20260707T123534Z/manual-review-selector/REPORT.md`
- `out/reports/remaining-link-fresh-selector-v3/20260707T123534Z/operator-review-packet/REPORT.md`

Accepted boundary: current selector evidence is ready for manual review only. The operator-review packet remains blocked by packet-shape mismatch (`dry_run_proposals must be a list`), so no approval manifest or live apply may be derived from this run without a follow-up adapter/code slice and verification.

## 2026-07-07 operator-review adapter acceptance note

Accepted: `operator_review_packet` can now consume `obslayer.manual-review-selector.v1` packets as a safe proposal-only evidence source.

Verification evidence:

- `out/reports/remaining-link-fresh-selector-v3/20260707T123534Z/operator-review-packet-adapter-v1/REPORT.md`
- focused test: `tests/test_operator_review_packet.py`
- full gate: `make verify`

Boundary: the adapter emits human-review evidence only. It does not create approval manifests, does not expose target paths, and does not authorize live vault mutation or apply.

- 2026-07-07: `remaining-link-fresh-selector-v3` operator acceptance recorded 25/25 manual-review candidates as evidence-only normalized Obsidian no-op link resolutions. Artifacts: `out/reports/remaining-link-fresh-selector-v3/20260707T123534Z/manual-acceptance-review-v1/REPORT.md` and `out/reports/remaining-link-fresh-selector-v3/20260707T123534Z/operator-acceptance-ledger-v1/REPORT.md`. No live apply authority or approval manifest was created.
- 2026-07-07: `full-vault-index-v1` built a read-only Memory-Vault index: 318 notes, 26 folders, 945 wikilinks, 858 resolved, 87 unresolved, 121 orphan notes, 0 duplicate-content groups. Artifacts: `out/reports/full-vault-index-v1/20260707T131041Z/REPORT.md`. Safety: no live mutation, no approval manifest, apply authority none.
- 2026-07-07: `broken-links-review-packet-v1` classified 87 unresolved links from full-vault index. Classes: {'protected_cross_vault_manual': 9, 'generated_report_auto_keep': 78}. Safety: no live mutation, no approval manifest, apply authority none. Artifacts: `out/reports/broken-links-review-packet-v1/20260707T132131Z/REPORT.md`.
- 2026-07-07: `protected-links-decision-v1` accepted 9 protected/cross-vault unresolved links as no-apply evidence: 8 concrete targets exist, 1 wildcard report pattern; no retarget/create/manifest/apply. Artifact: `out/reports/broken-links-review-packet-v1/20260707T132131Z/protected-links-decision-v1/REPORT.md`.
