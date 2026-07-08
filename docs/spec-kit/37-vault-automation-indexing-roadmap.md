# 37 — Vault Automation Indexing Roadmap

Status: active roadmap
Date: 2026-07-05
Scope: fixation of the current full-vault indexing stop point, external research, Nanobot/Codex review signals, and the next repo-only automation slices

## Decision

Continue from the latest full-vault index as a **repo-only automation buildout**, not as live vault cleanup.

The routing contract for proposal automation is explicit:

```text
suggest -> auto-propose -> needs-human-review -> blocked/refuse
```

The next work is:

```text
lane-schema-v1 → candidate-scorer-v1 → archive-shadow-index → decision-ledger-v1 → auto-proposal thresholds → approved apply only after separate explicit approval
```

No component may jump from index/scoring directly to live note mutation.

## Standing safe-pattern approval — deterministic link-prefix hygiene

Operator decision: Dmitry approved automatic continuation for the deterministic link-prefix hygiene pattern proven in the July 2026 live batches. The allowed pattern is narrow:

```text
[[Hermes/<title>]] -> [[Memory-Vault/Hermes/<title>]]
```

Only when all gates are true:

1. The source occurrence is read from the current live file immediately before proposal creation.
2. The exact target note exists at `Memory-Vault/Hermes/<title>.md`.
3. The source file is a normal Memory note, not generated report/history/noise and not a protected path.
4. The proposal binds the full-file base SHA256.
5. The apply uses the approved backup namespace `_Backups/obsidian-operating-layer`.
6. Post-verify is required and must pass.
7. Any drift, missing target, duplicate/no-op ambiguity, protected path, or verification issue stops the batch.

Generated reports remain suppressed from routine auto-apply even when exact candidates exist; they can be handled only by a separate explicit decision because they are historical evidence surfaces.

This standing approval does not cover creates, deletes, renames, moves, archive rewrites, Soul/cross-vault retargeting, semantic/global replacements, external-tool writes, scheduled jobs, or other destructive/high-risk operations.

Repo codification follow-up: the standing policy is now backed by a reusable read-only baseline tool, `tools/obsidian_standing_safe_link_prefix_baseline.py`, and package helper `obslayer.standing_safe_link_prefix_baseline`. The tool scans a vault or scan root without writing, emits JSON/Markdown evidence, and always reports `live_mutation_authorized: false`, `approval_manifest_created: false`, and `apply_authority: none`. Current live read-only baseline evidence is under `out/reports/standing-safe-link-prefix-baseline/live-current/`; it reports zero allowed/actionable candidates and only excluded generated/protected surfaces.


R13 reconciliation note: after the standing baseline tool landed, the current project state is `DB = Kanban state`, `docs = accepted policy/mirror`, and `out/ = evidence`. `out/reports/manifest-candidate-selector/grouped-next5-smoke/` remains historical/stale for any future apply manifest; fresh selector evidence against current live-read inputs is required before drafting any new approval manifest.

## Current indexing stop point

Authoritative generated evidence:

- Full vault index: `out/reports/full-vault-index-analysis/20260705T084734Z/`
- Research synthesis: `out/reports/vault-automation-research/20260705T090600Z/`
- Document audit: `out/reports/document-audit/20260705T122800Z/`

Current full-vault metrics:

| Metric | Count |
|---|---:|
| Markdown files | 1121 |
| Wikilinks total | 12979 |
| Wikilinks OK | 1493 |
| Wikilinks broken | 7434 |
| Wikilinks ambiguous | 4052 |
| Duplicate title groups | 210 |
| Exact duplicate content groups | 163 |
| Archive collision title groups | 181 |
| Orphan non-archive notes | 376 |

Active Memory focus:

| Lane | Count |
|---|---:|
| `active_memory_broken` | 593 |
| `active_memory_ambiguous` | 779 |
| `active_memory_ambiguous_memory_plus_archive` | 505 |
| `active_memory_ambiguous_other` | 274 |

## External / agent review signals incorporated

- Obsidian API: use native semantics as compatibility evidence (`MetadataCache.resolvedLinks/unresolvedLinks`, `generateMarkdownLink`, `FileManager.renameFile` behavior), not as uncontrolled write owner.
- Dataview: model vault as a queryable database/reporting layer.
- Obsidian Linter: rule toggles and conservative formatting automation pattern.
- Wikilink Linter: preview-before-write and skip-ambiguous behavior are reference safety patterns.
- Vault Inspector: read-only CLI audit model for health checks.
- Vault Doctor / broken-link plugins: useful health/preview patterns; bulk remove/cleanup behavior is unsafe without our gate.
- Codex review: broad full-vault auto-apply is unsafe; automation should improve observe/index/classify/score/propose/verify.
- Nanobot review: graph-first, embedding-later; human gate for Soul/archive/memory/canonical, redirects/duplicates, renames/merges/deletes/global replacements, and high-volume batches.
- Independent Nanobot-style delegated audit `deleg_3248b6f9`: confirmed the roadmap direction and reframed the current stop as candidate/link-resolution quality, not a runtime blocker.

## Non-negotiable safety boundary

Live vault mutation remains allowed only through:

```text
observe → propose → review → explicit approval → backup → apply → verify
```

Hard stops:

- no live apply from this roadmap;
- no auto-create, rename, merge, delete, or global replacement;
- no mutation of `_Archive`, `_Backups`, `Duplicates`, `Redirects`, `.obsidian`, `.trash`, or Soul-protected surfaces;
- no embeddings as an authority for edits;
- no external component owns live writes;
- no secrets or note-body dumps in generated reports.

## Roadmap from the current indexing point

### R0 — freeze evidence and doc state

Status: done by this document and the document audit.

Deliverables:

- current metrics fixed in spec-kit;
- evidence pointers registered;
- docs audited for relative-link integrity.

Acceptance:

- `out/reports/document-audit/20260705T122800Z/REPORT.md` exists;
- `git diff --check` passes;
- no live vault mutation performed.

### R1 — `lane-schema-v1`

Status: accepted as a repo-only/operator packet layer.

Goal: make all indexing lanes machine-readable for Hermes/Codex/Nanobot and future dashboards.

Deliverables:

- schema: lane id, source class, issue type, count, allowed next action, forbidden actions, approval class, confidence policy, sensitive-surface flags;
- converter from `actionable-lanes.json` into versioned lane packets;
- generated lane queue under `out/lanes/` or `out/reports/lane-schema-v1/`.

Acceptance evidence:

- implementation: `src/obslayer/lane_schema_v1.py`;
- CLI: `tools/obsidian_lane_schema_v1.py`;
- tests: `tests/test_lane_schema_v1.py`;
- current generated packet: `out/reports/lane-schema-v1/20260705T171353Z/lane-schema-packet.json`;
- current generated report: `out/reports/lane-schema-v1/20260705T171353Z/REPORT.md`.

Accepted boundary:

- validates the four current next lanes: `active_memory_ambiguous_memory_plus_archive`, `active_memory_broken`, `archive_or_backup_noise`, `active_soul_source`;
- records source class, issue type, count, allowed next action, forbidden actions, approval class, confidence policy, sensitive-surface flags, and `live_mutation_authorized: false`;
- marks archive/backup and Soul lanes as report-only/human-gated;
- creates no approval manifest and no live mutation target.

### R2 — `archive-shadow-index`

Status: accepted repo-only/evidence-only slice after `tests/test_archive_shadow_index.py` passes.

Acceptance evidence: `src/obslayer/archive_shadow_index.py`, `tools/obsidian_archive_shadow_index.py`, `tests/test_archive_shadow_index.py`, and `out/reports/archive-shadow-index/20260705T173124Z/REPORT.md`.

Accepted boundary: emits `archive-shadow-index.json` and `REPORT.md`; keeps `live_mutation_authorized: false`, `approval_manifest_created: false`, `targets: []`, and no apply authority; treats archive, backup, duplicate, and redirect shadows as evidence-only, never as active replacement targets.

Goal: prevent archive/backup/duplicate/redirect notes from being treated as equal targets to active notes.

Deliverables:

- shadow index of `_Archive`, `_Backups`, `Duplicates`, `Redirects`, retired/canonical collisions;
- reason codes: `active_target_available`, `archive_shadow_only`, `memory_plus_archive_collision`, `redirect_collision`, `duplicate_title_group`;
- resolver rule: archives, backups, duplicates, and redirects are evidence-only by default;
- generated artifacts: `archive-shadow-index.json` and `REPORT.md`.

Acceptance:

- covers 181 archive collision title groups;
- explains 505 active Memory `memory+archive` ambiguous cases;
- does not propose archive targets as default active replacements;
- keeps `live_mutation_authorized: false`, `approval_manifest_created: false`, `targets: []`, and no apply authority.

### R3 — `candidate-scorer-v1`

Status: accepted as a repo-only/evidence-only scorer packet and CLI writer.

Acceptance evidence: `src/obslayer/candidate_scorer_v1.py`, `tools/obsidian_candidate_scorer.py`, `tests/test_candidate_scorer_v1.py`, and `out/reports/candidate-scorer-v1/20260705T175815Z/REPORT.md`.

Accepted boundary: emits `candidate-scorer-v1.json` and `REPORT.md`; keeps `mode: repo-only/evidence-only`, `behavior: evidence-only`, `live_mutation_authorized: false`, `approval_manifest_created: false`, `targets: []`, and `apply_authority: none`. It scores candidate evidence only and never creates approval manifests or live apply targets.

Current generated summary from `out/reports/full-vault-index-analysis/20260705T084734Z/`: 779 candidate packets, 3,699 candidates, 779 review-required packets, 779 hard-stop packets, and max top-two gap 135.

Implemented features:

- reason codes on every packet and candidate;
- feature breakdown on every candidate;
- top-two candidate gap on every packet;
- archive, backup, duplicate, redirect, canonical, missing, Soul, and protected candidates remain review-required or hard-stop/human-gated;
- no candidate grants live apply authority.

Confidence bands:

| Band | Score | Allowed | Forbidden |
|---|---:|---|---|
| deterministic-high | `>= 0.95` | `auto-propose` | live apply without explicit approval |
| review-medium | `0.75-0.95` | `needs-human-review` | manifest without human review |
| evidence-low | `< 0.75` | `suggest` | patch proposal by default |

The `blocked/refuse` route is reserved for protected surfaces, hard-stop risk codes, or any attempted authority over live apply / approval-manifest creation.

### R3b `semantic-manifest-doctor`

Status: accepted repo-only/read-only doctor for existing semantic indexing manifests.

Acceptance evidence: `src/obslayer/semantic_manifest.py`, `tools/obsidian_semantic_manifest_doctor.py`, `tests/test_semantic_manifest.py`, `out/reports/semantic-manifest-doctor/codex-implementation/REPORT.md`.

Accepted boundary: reads one supplied semantic manifest JSON under repo `out/`, verifies `mode: semantic-indexing-manifest`, mutation and approval flags false, non-empty artifact list, artifact paths under repo `out/`, and empty manifest findings; returns `ready` or `blocked` only and never rebuilds evidence, scans the live vault, creates approval manifests, or applies changes.

### R4 — `operator-decision-ledger-v1`

Status: accepted as a repo-only/evidence-only append-only decision ledger bundle and CLI writer.

Acceptance evidence: `src/obslayer/operator_decision_ledger_v1.py`, `tools/obsidian_operator_decision_ledger.py`, `tests/test_operator_decision_ledger_v1.py`, and `out/reports/operator-decision-ledger-v1/20260705T180705Z/REPORT.md`.

Accepted boundary: emits `operator-decision-ledger-v1.json`, `operator-decisions.jsonl`, and `REPORT.md`; keeps `behavior: evidence-only`, `live_mutation_authorized: false`, `approval_manifest_created: false`, and `targets: []`. Approval manifests and target paths may be cited only as inert evidence references.

Goal: turn approve/reject/held decisions into reusable scoring evidence.

Deliverables:

- append-only ledger schema;
- entries for source pattern, proposed target, decision, reason, scorer version, verification outcome;
- JSONL/JSON loader plus CLI/report writer;
- loader that influences future scoring without storing secrets or raw note bodies.

Acceptance:

- prior decisions can be replayed into scorer features;
- ledger is repo-local and reviewable;
- JSONL records remain normalized, sorted, and append-friendly;
- reject/held decisions lower confidence on matching future candidates;
- records never create approval authority, live apply authority, or live vault targets.

### R5 — `safe-auto-proposal-thresholds`

Status: accepted as a repo-only/evidence-only dry-run proposal threshold packet and CLI writer.

Acceptance evidence: `src/obslayer/safe_auto_proposal_thresholds_v1.py`, `tools/obsidian_safe_auto_proposal_thresholds.py`, `tests/test_safe_auto_proposal_thresholds_v1.py`, and `out/reports/safe-auto-proposal-thresholds-v1/20260705T181910Z/REPORT.md`.

Accepted boundary: consumes `candidate-scorer-v1` packets and emits `safe-auto-proposal-thresholds-v1.json`, `dry-run-proposals.jsonl`, and `REPORT.md`; keeps `behavior: evidence-only`, `live_mutation_authorized: false`, `approval_manifest_created: false`, `approval_manifest_authority: false`, `targets: []`, and `apply_authority: none`. Current full-vault evidence produced `0` dry-run proposals and held all `779` scored links for review.

Goal: raise automation without bypassing review/apply gates.

Deliverables:

- auto-generation of dry-run proposal bundles only for deterministic-high, non-sensitive, non-archive-collision candidates;
- dry-run proposal candidates with file, position, old link, proposed link, confidence, reason, policy tag, and rollback key;
- held-for-review ledger for unsafe/uncertain candidates.

Acceptance:

- zero live writes;
- no approval manifests, live targets, or apply authority;
- no Soul/archive/global/rename/delete/merge candidates in auto-proposal lane;
- proposal includes file, position, old link, proposed link, confidence, reason, policy tag, rollback key;
- current full-vault candidate scorer input is safely held because no candidate meets deterministic auto-proposal gates.

### R6 — external-tool benchmark

Status: accepted as a repo-only/evidence-only deterministic read-only simulation/comparison against external-tool behavior patterns.

Acceptance evidence: `src/obslayer/external_tool_benchmark.py`, `tools/obsidian_external_tool_benchmark.py`, `tests/test_external_tool_benchmark.py`, and `out/reports/external-tool-benchmark/20260705T183948Z/REPORT.md`.

Accepted boundary: consumes current `candidate-scorer-v1` packet shapes (`scored_links` / `candidate_packets`) and emits `external-tool-benchmark.json` plus `REPORT.md`; no external tool subprocess, API, or write mode is executed. Differences become scorer test cases/proposal-only records, with `behavior: evidence-only`, `live_mutation_authorized: false`, `approval_manifest_created: false`, and `targets: []`.

Goal: compare our scanner/scorer against external tools while keeping write rights disabled.

Tools/patterns:

- Wikilink Linter preview/skip ambiguous;
- Vault Inspector read-only audit;
- Obsidian API link semantics;
- Dataview-like query surfaces.

Acceptance:

- benchmark report under `out/reports/external-tool-benchmark/`;
- any tool with write capability is run only in no-write/sandbox/read-only mode;
- differences become scorer test cases, not direct edits.

### R7 — narrow approved apply pilot, only after separate approval

Status: repo-only readiness gate accepted; live apply remains blocked without a fresh explicit approval manifest.

Acceptance evidence for readiness gate: `src/obslayer/approved_apply_readiness_v1.py`, `tools/obsidian_approved_apply_readiness.py`, `tests/test_approved_apply_readiness_v1.py`, and `out/reports/approved-apply-readiness-v1/20260705T185155Z/REPORT.md`.

Accepted readiness boundary: validates a proposal/approval-manifest bundle without applying it; checks proposal-manifest path alignment, vault-root agreement, protected target refusal, hash binding, evidence references, target count, backup-root policy, and post-verify requirement; emits `approved-apply-readiness-v1.json` and `REPORT.md` with `behavior: readiness-only/evidence-only`, `live_mutation_authorized: false`, `approval_manifest_created: false`, `approval_manifest_authority: false`, `targets: []`, and `apply_authority: none`.

Goal: prove end-to-end apply readiness on a tiny safe batch after the repo-only layers are stable.

Preconditions for any future live apply:

- R1–R6 accepted;
- generated proposal reviewed;
- explicit approval manifest exists for that exact proposal;
- readiness gate passes;
- backup root and expected hashes are present;
- batch size starts at 1–5 files.

Acceptance for actual live apply, only after separate explicit approval:

- backup created;
- apply is hash-bound;
- fresh post-verify shows no unexpected regression;
- rollback evidence exists;
- metrics diff is recorded.

### R8 — acceptance bundle doctor

Status: accepted as a repo-only evidence/readiness safety gate.

Acceptance evidence: `src/obslayer/acceptance_bundle_doctor.py`, `tools/obsidian_acceptance_bundle_doctor.py`, `tests/test_acceptance_bundle_doctor.py`, and `docs/spec-kit/41-acceptance-bundle-doctor.md`.

Accepted boundary: validates a repo-local acceptance bundle and required checks before any future apply-readiness step; keeps `live_mutation_authorized: false`, `approval_manifest_created: false`, `apply_authority: none`, and `targets: []`; refuses live target paths and artifacts outside allowed repo roots.

### R9 — operator review packet

Status: accepted as a repo-only post-readiness human-review checkpoint.

Acceptance evidence: `src/obslayer/operator_review_packet.py`, `tools/obsidian_operator_review_packet.py`, `tests/test_operator_review_packet.py`, and `docs/spec-kit/42-operator-review-packet.md`.

Accepted boundary: consumes dry-run proposal evidence under repo `out/` and emits `operator-review-packet.json` plus `REPORT.md`; keeps `live_mutation_authorized: false`, `approval_manifest_created: false`, `approval_manifest_authority: false`, `target_paths: []`, and `apply_authority: none`. Empty dry-run proposal evidence becomes `no_candidate` and must not be turned into an approval request.

### R10 — unified operator review index

Status: accepted as a repo-only control panel.

Acceptance evidence: `src/obslayer/unified_operator_review_index.py`, `tools/obsidian_unified_operator_review_index.py`, `tests/test_unified_operator_review_index.py`, `docs/spec-kit/47-unified-operator-review-index.md`, and `out/reports/unified-operator-review-index/full-vault-proposal-only-20260706T182612Z/REPORT.md`.

Accepted boundary: aggregates only repo-local `out/` and docs pointers; missing pointers are visible, unsafe authority flags block; it never creates approval manifests, never writes the vault, and keeps `target_paths: []`.

### R11 — candidate-volume operator packet

Status: accepted as a repo-only operator gate over the latest proposal-only evidence.

Acceptance evidence: `src/obslayer/candidate_volume_operator_packet.py`, `tools/obsidian_candidate_volume_operator_packet.py`, `tests/test_candidate_volume_operator_packet.py`, `docs/spec-kit/48-candidate-volume-operator-packet.md`, and `out/reports/candidate-volume-operator-packet/full-vault-proposal-only-20260706T182612Z/REPORT.md`.

Accepted boundary: summarizes observation/proposal/verify/unified-index evidence, protected buckets, and route buckets; it reports candidate volume but deliberately leaves `first_manifest_candidate_queue: []` and grants no apply authority.

### R12 — manifest-candidate selector

Status: accepted repo-only selector smoke after independent read-only Codex review.

Acceptance evidence: `src/obslayer/manifest_candidate_selector.py`, `tools/obsidian_manifest_candidate_selector.py`, `tests/test_manifest_candidate_selector.py`, `docs/spec-kit/49-manifest-candidate-selector.md`, and `out/reports/manifest-candidate-selector/grouped-next5-smoke/HERMES_ACCEPTANCE.md`, and Codex review `manifest-selector-independent-review-20260707T044711Z.codex_report.json`.

Accepted boundary: consumes existing repo-local JSON evidence, selects at most five review candidates, refuses missing/blocked/authority-bearing inputs, and emits no approval manifest, target paths, or apply authority.

### R13 — reconciliation gate

Status: active docs/acceptance consolidation gate.

Goal: keep the acceptance index, roadmap, evidence index, and orchestration board aligned with the packet/index/doctor taxonomy before opening another implementation slice.

Acceptance:

- current packet/index/doctor taxonomy is present in `docs/acceptance/index.md`;
- R10-R12 are represented in this roadmap;
- current evidence index has a reconciliation note with pending gates;
- fresh selector v2 and operator nextgate evidence are recorded as manual-only/no-apply current-state pointers;
- remaining-link fresh selector validation stays proposal-only and does not create apply authority;
- `git diff --check` and `make verify` pass.


## Lane priority

1. `active_memory_ambiguous_memory_plus_archive` — first scorer target because it is the main blocker and should be solvable by archive-shadow rules.
2. `active_memory_broken` — target discovery only; no auto-create.
3. `archive_or_backup_noise` — report/index only; no mutation.
4. `active_soul_source` — policy-sensitive; report only unless explicitly approved.
5. generated Graphify/report surfaces — treat as noise/corpus evidence unless a separate Graphify cleanup task is approved.

## Acceptance checklist for the next implementation slice

- [ ] Inputs reference the current index run and research synthesis.
- [ ] Outputs are under `out/` or schemas/docs in repo only.
- [ ] `live_mutation_authorized: false` is present in generated packets.
- [ ] Archive/backup/Soul surfaces are classified before scoring.
- [ ] Every candidate has confidence, reason codes, and risk gates.
- [ ] Every candidate is routed into one of `suggest`, `auto-propose`, `needs-human-review`, or `blocked/refuse`.
- [ ] `git diff --check` passes.
- [ ] Relevant tests or `make verify` pass if code/schema behavior changes.
- [ ] Nanobot/Codex may review, but Hermes remains acceptance owner.

## Current open risks

- Full corpus is noisy because generated Graphify reports and backups dominate broken-link counts.
- Duplicate titles and archive collisions are too numerous for title-only replacement.
- Human memory/canonical Soul surfaces require conservative gates even when scores are high.
- Existing docs have a duplicate numeric prefix `29`; avoid adding further numbering ambiguity.

## Current closure state

R1–R13 are closed/accepted for the current repo-only control-plane sequence. Do not reopen historical lanes such as `lane-schema-v1`, archive shadow index, candidate scorer, operator decision ledger, safe thresholds, or R13 standing-baseline reconciliation unless a fresh regression explicitly invalidates their accepted evidence.

Standing link-prefix baseline integration is closed as a read-only/operator evidence surface:

- canonical tool: `tools/obsidian_standing_safe_link_prefix_baseline.py`;
- current evidence: `out/reports/standing-safe-link-prefix-baseline/live-current/REPORT.md`;
- current result: `allowed_count: 0`, `actionable_apply_items: 0`;
- authority: `live_mutation_authorized: false`, `approval_manifest_created: false`, `apply_authority: none`.

Historical selector output such as `grouped-next5` is stale for any new apply manifest because those links were already applied and verified.

### Source-of-truth sequence for continuation

Use this sequence before any new OOL work:

1. Check repo state and Kanban DB nonclosed cards.
2. Read `docs/acceptance/index.md` and mark accepted layers as closed/historical.
3. Read this roadmap's current closure and next target.
4. Read `docs/spec-kit/36-current-evidence-index.md` for current evidence pointers and stale-output warnings.
5. Read `docs/triage/kanban-board.md` as the human mirror of DB/runtime closure.
6. Only then create or resume cards. Do not create a swarm for an already accepted layer.

Nanobot/scout reports are useful review inputs, but closure happens only when the accepted decision is mirrored into source-controlled docs and the board card is `done`, `cancelled`, or `archived`.

## Next command-level target

The next technical gate is a fresh selector/regeneration pass against current evidence for remaining broken/ambiguous link discovery, suppression, and operator review. That pass must produce new current-input evidence before Hermes proposes any tiny explicit approval manifest for Dmitry to approve or reject.

Live vault mutation remains blocked until Dmitry approves a fresh manifest for a specific proposal, except the recorded standing safe-pattern deterministic link-prefix hygiene policy. That exception is narrow: exact current-file replacement, existing target, protected/report/Soul exclusions, approval manifest, backup, and post-verify.

## 2026-07-07 scorer follow-up closure

`remaining-link-scorer-improvement-v1` is accepted as a small repo-only scorer hardening slice following the bounded sandbox selector result. It strengthens deterministic source-context weighting and adds regression coverage for same-vault ranking against archive hard-stop competitors.

Evidence:

- `out/reports/remaining-link-scorer-improvement-v1/final-report/REPORT.md`
- `src/obslayer/candidate_scorer_v1.py`
- `tests/test_candidate_scorer_v1.py`

Boundary: proposal/scoring only; no approval manifest, no target authorization, no live vault mutation.

Next real work remains fresh selector/regeneration/operator-review over current remaining-link evidence; any live apply still requires a fresh exact manifest and approval unless it falls within the already-approved bounded link-hygiene pattern.

## 2026-07-07 fresh selector v3 current state

Fresh selector/regeneration over current remaining-link evidence has been rerun after scorer hardening.

Evidence:

- `out/reports/remaining-link-fresh-selector-v3/20260707T123534Z/REPORT.md`
- `out/reports/remaining-link-fresh-selector-v3/20260707T123534Z/candidate-scorer/candidate-scorer-v1.json`
- `out/reports/remaining-link-fresh-selector-v3/20260707T123534Z/manual-review-selector/manual-review-selector-v1.json`
- `out/reports/remaining-link-fresh-selector-v3/20260707T123534Z/operator-review-packet/REPORT.md`

Current result: manual selector is `ready_for_manual_review` with 25 review items, all repo-only/proposal-only. Operator packet generation is blocked on an evidence-shape adapter gap (`dry_run_proposals must be a list`) because the current operator review CLI expects dry-run proposal packets, not manual-selector packets.

Next technical gate: implement or route through a small adapter that converts manual-selector review items into an operator-review-compatible evidence packet, preserving `live_mutation_authorized: false`, `approval_manifest_created: false`, `apply_authority: none`, and empty target authorization.

## 2026-07-07 operator-review adapter gate closed

The manual-selector-to-operator-review adapter gap from fresh selector v3 has been closed in the existing operator review packet builder rather than by adding a new architecture layer.

Evidence:

- `out/reports/remaining-link-fresh-selector-v3/20260707T123534Z/operator-review-packet-adapter-v1/REPORT.md`
- `out/reports/remaining-link-fresh-selector-v3/20260707T123534Z/operator-review-packet-adapter-v1/operator-review-packet.json`

Current state: fresh remaining-link selector evidence can now advance to operator-review packet form (`ready_for_human_review`, 25 items, no findings) while preserving no-apply/no-live-mutation guardrails. Next gate remains human review / explicit approval manifest design; no live vault mutation is authorized by this adapter.

- 2026-07-07: Fresh selector v3 manual-review batch now has operator acceptance evidence for 25 normalized no-op link resolutions; next automation work should avoid generating live apply manifests for normalized Obsidian no-op cases and reserve approval manifests for concrete replacement targets.
- 2026-07-07: `full-vault-index-v1` built a read-only Memory-Vault index: 318 notes, 26 folders, 945 wikilinks, 858 resolved, 87 unresolved, 121 orphan notes, 0 duplicate-content groups. Artifacts: `out/reports/full-vault-index-v1/20260707T131041Z/REPORT.md`. Safety: no live mutation, no approval manifest, apply authority none.
- 2026-07-07: `broken-links-review-packet-v1` classified 87 unresolved links from full-vault index. Classes: {'protected_cross_vault_manual': 9, 'generated_report_auto_keep': 78}. Safety: no live mutation, no approval manifest, apply authority none. Artifacts: `out/reports/broken-links-review-packet-v1/20260707T132131Z/REPORT.md`.
- 2026-07-07: `protected-links-decision-v1` accepted 9 protected/cross-vault unresolved links as no-apply evidence: 8 concrete targets exist, 1 wildcard report pattern; no retarget/create/manifest/apply. Artifact: `out/reports/broken-links-review-packet-v1/20260707T132131Z/protected-links-decision-v1/REPORT.md`.
## 2026-07-08 Graphify incremental index docs-lag closure

`graphify_incremental_index` is recorded as a minimal repo-only indexing wrapper: it reuses existing Graphify handoff, embedding-run, and query-smoke components, selects delta candidates, and defaults to dry-run. It is not an indexing control-plane rewrite and does not authorize live vault mutation, approval manifests, targets, cron/service changes, or embedding runs without the existing resource gates.

Evidence:

- `src/obslayer/graphify_incremental_index.py`
- `tools/obsidian_graphify_incremental_index.py`
- `tests/test_graphify_incremental_index.py`

Nanobot proposals deliberately retained for later review, not implemented here: unified indexing control plane, operator dashboard / "what changed since last scout", and index freshness contract.
