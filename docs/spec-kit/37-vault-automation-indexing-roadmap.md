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

Goal: prove end-to-end apply on a tiny safe batch after the repo-only layers are stable.

Preconditions:

- R1–R5 accepted;
- generated proposal reviewed;
- explicit approval manifest exists;
- backup root and expected hashes are present;
- batch size starts at 1–5 files.

Acceptance:

- backup created;
- apply is hash-bound;
- fresh post-verify shows no unexpected regression;
- rollback evidence exists;
- metrics diff is recorded.

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

## Next command-level target

Implement R1–R3 as a repo-only slice:

```text
schemas/lane-schema.v1.json
src/obslayer/lane_schema.py
tools/obsidian_lane_queue.py
src/obslayer/archive_shadow_index.py
tools/obsidian_candidate_scorer.py
out/reports/lane-schema-v1/<run>/
out/reports/candidate-scorer-v1/<run>/
```

This is the next safe continuation point from indexing.
