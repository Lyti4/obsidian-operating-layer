# 24 — Orchestration Backlog

Status: active orchestration plan  
Date: 2026-07-02  
Scope: finish, harden, improve, and begin applying Obsidian Operating Layer layer by layer.

## Purpose

This backlog converts the architecture/spec/acceptance documents into an execution order for Hermes-as-orchestrator.

The project should advance through narrow, verifiable slices. Live Obsidian mutation stays gated by explicit approval manifests.

## Layer map and definition of done

| Layer | Definition of done | Current status | Next slice |
|---|---|---|---|
| Safety core | protected paths, approval manifest, backup, drift verify, fail-closed tests | baseline accepted | keep regression tests green |
| Observe/propose/verify/apply | stable CLI, JSON + Markdown artifacts, dry-run default | baseline accepted | smoke live read-only proposal flow |
| Review/operator UX | list/explain, review bundle, decision record, runbooks | mostly accepted | use on real proposal-only pass |
| Sandbox layer | disposable copies, protected-path exclusions, reset controls | baseline accepted | medium sandbox indexing probe |
| Indexing/MCP/RAG | guarded wrapper, sanitized reports, derived storage, batching/resume, final468 semantic query smoke | final468 sandbox/derived-cache accepted | productize repeatable query/proposal reports; routine unattended indexing still gated |
| Docs/productization | release gate, acceptance index, runbooks, changelog | productization slice added | keep docs in sync after each slice |
| Application layer | proposal-only live operation, then approved narrow apply | P3 proposal-only pass green | optional narrow approved apply after explicit manifest |

## Execution rules

1. Start every slice with `make verify` unless the slice is docs-only and already verified in the same session.
2. Prefer sandbox/read-only/proposal-only over live apply.
3. Use Codex/subagents for complex code changes and Hermes for orchestration, review, docs, and acceptance.
4. Do not promote external adapters without an adapter-specific scorecard.
5. Every accepted slice must name evidence artifacts and rollback/disable conditions.

## Priority backlog

### P0 — restore and freeze current green baseline

- Keep `make verify` green.
- Review current uncommitted indexing/runtime changes.
- Ensure `git diff --check` stays clean.
- Decide whether the current indexing runtime changes are one commit or split commits.

### P1 — productization surface

- Maintain `docs/release-readiness.md` as the release go/no-go gate.
- Maintain `docs/acceptance/index.md` as the accepted boundary map.
- Keep short runbooks under `docs/runbooks/`.
- Add release notes under `docs/releases/` for each accepted slice.

### P2 — indexing runtime stabilization

Status: accepted for the current Graphify-derived final468 sandbox/derived-cache pass. The old medium/full sandbox probe wording is superseded by the 2026-07-04 final468 evidence.

Done:
- Graphify-derived sandbox handoff created a bounded manifest.
- Local Ollama `bge-m3` embedding run completed in safe batches.
- Final counts: `468` records, `467` processed, `1` skipped empty file, `467` embedding sidecars, `3605` query-smoke chunks, `0` missing embeddings.
- Semantic query smoke succeeded and is reusable through `tools/obsidian_graphify_embedding_query.py`.
- `docs/spec-kit/20-indexing-runtime-acceptance.md` and `27-graphify-nanobot-embedding-orchestration.md` record the accepted boundary.

Still gated:
- routine unattended semantic indexing;
- live vault mutation from semantic findings;
- external/cloud embeddings without explicit approval.

### P3 — first real usage without mutation

- Run live vault observation read-only.
- Generate a proposal-only bundle for one low-risk improvement/report.
- Review with dashboard/explain.
- Do not apply unless a separate approval manifest is explicitly approved.

### P4 — narrow approved apply

Only after P3 produces a useful proposal and the operator approves:

- create exact approval manifest;
- require canonical `backup_root: "_Backups/obsidian-operating-layer"`;
- backup;
- apply;
- run mandatory post-apply content verification;
- post-observe;
- verify drift;
- record release note and acceptance update.

### P5 — refactor and portability

- Parameterize hardcoded local paths where practical.
- Split `tools/obsidian_indexing_stdio_probe.py` into smaller modules after behavior is frozen.
- Add integration checks for critical make targets.
- Reduce wrapper duplication only if it simplifies maintenance without breaking operator muscle memory.

## Stop conditions

Stop and report instead of continuing if:

- `make verify` fails;
- a sanitized report leaks secrets or raw live/sandbox/derived absolute paths;
- an external adapter declares write/delete/move capability unexpectedly;
- live vault fingerprint changes during a read-only/sandbox/proposal-only slice;
- an approval manifest does not exactly match proposal targets.

## Reporting format

Use the concise operator format:

```text
Сделано: ...
Проверка: ...
Осталось: ...
Риск/блокер: ...
Следующий шаг: ...
```


### 2026-07-02 P3 live proposal-only pass

Result: green read-only/proposal-only run.

Evidence:
- `make verify` passed before the run.
- Observation/proposal/verification artifacts: `out/live-proposal-only-20260702T093117Z/`.
- Live vault scan observed 1048 Markdown files and related non-Markdown assets.
- Generated proposal stayed `mode: dry-run`, `dry_run_default: true`, `approval_required: true`, `risk_class: read_only_only`, with `0` targets.
- Verification returned `ok: true` and no issues.
- Post-run mtime check found `0` live vault files modified since run start.
- Generated artifacts had no secret-pattern hits.

Finding:
- The runbook used stale CLI flags/paths; updated to current `--observe`, `--out-dir`, and verify command behavior.


### 2026-07-02 P3 repeatable make target

Result: green repeatable read-only/proposal-only target.

Changes:
- Added `make live-proposal-only` for timestamped observation/proposal/verification artifacts under `out/live-proposal-only-*`.
- Added `obsidian_verify.py --json-only` so verification artifacts are machine-readable without stripping human status text.
- Updated the observe/propose/verify runbook to prefer the make target and keep manual commands as an equivalent path.

Evidence:
- `make verify` passed.
- Tiny temp-vault run passed and produced JSON-only verification.
- Live read-only run: `out/live-proposal-only-20260702T095004Z/`.
- Live run observed 1048 Markdown files, produced `0` proposal targets, kept `dry_run_default: true`, and verification returned `ok: true` with no issues.
- Post-run mtime check found `0` live vault files modified since run start.


### 2026-07-02 P4 sandbox apply-contract preflight

Result: green sandbox-only apply contract preflight; live apply remains blocked pending explicit approval manifest.

Evidence:
- Created a temporary vault under `/tmp` with one note target.
- Built a proposal with one text replacement, `base_sha256`, evidence, and dry-run defaults.
- Built an approval manifest naming the exact proposal and target, with `APPROVE OBSIDIAN APPLY`, `dry_run: false`, and `require_post_verify: true`.
- `obsidian_apply.py` dry-run returned `status: dry-run` and did not create backups.
- Approved sandbox apply returned `status: applied`, changed exactly one temp-vault note, and created a backup copy under the temp vault `_Backups/obsidian-operating-layer/...`.
- No live Obsidian vault path was used for the apply preflight.

Finding:
- `docs/runbooks/approved-live-apply.md` used stale CLI flags. Updated it to the actual `obsidian_apply.py` and `make live-proposal-only` commands.


### 2026-07-02 P4 fail-closed apply contract hardening

Result: sandbox-only guardrail hardening completed.

Changes:
- Approval manifests must use the canonical backup root `_Backups/obsidian-operating-layer`.
- Example approval manifests were updated to the current live-apply schema and exact proposal binding.
- `obsidian_apply.py` records mandatory `post_verify` evidence after approved apply.
- Added fail-closed regression coverage for wrong backup roots, extra approved targets, and missing proposal targets.

Evidence:
- `python3 -m pytest tests/test_guardrails.py tests/test_apply_rehearsal.py -q` passed.
- Live Obsidian vault was not mutated.

### P2b — Graphify-first semantic layer

- Use Nanobot as the Graphify worker through the subscription bridge on `gpt-5.4-mini`.
- Run only on sandbox/read-only vault snapshots.
- Produce graph/report/proposal artifacts under `out/`.
- Verify no live vault mutation, no protected-path target, no secret leakage, and no automatic embedding job.
- Use Graphify outputs to select a narrow embedding candidate set later.
- Do not run routine/full embeddings until a separate bounded embedding slice is approved.

Reference contract: `25-nanobot-graphify-worker.md`.

### P2c — Nanobot standing maintenance and communication layer

- Use Nanobot as a supervised standing worker for project maintenance, status checks, task packet routing, and proposal-only reports.
- Keep Hermes as acceptance owner and user-facing decision maker.
- Store persistent task artifacts under `out/queue/`, `out/reports/`, and `out/proposals/`.
- Do not create cron jobs, restart services, install third-party apps, mutate auth, or run embeddings without separate explicit user approval.
- Verify every Nanobot result for scope, secret hygiene, protected paths, live mutation absence, and evidence quality.

Reference contract: `26-nanobot-standing-worker.md`.

### 2026-07-02 Nanobot compliance excerpt review

Result: green read-only Nanobot compliance review using sanitized excerpts instead of expanding Nanobot workspace access.

Evidence:
- Runtime health checked for Nanobot and Headroom.
- Current Nanobot routing is governed by `28-global-headroom-only-llm-channel.md` and uses only the `nanobot-headroom-agent` wrapper.
- Artifacts: `out/reports/nanobot-standing-worker/20260702-compliance-excerpts/`.
- Secret-pattern scan over generated artifacts returned no findings.
- Live vault was not mutated; Nanobot did not write into the repository directly.

Follow-up changes:
- Clarified internal vs sanitized path reporting.
- Normalized protected-path inheritance for Graphify tasks.
- Added explicit bridge fallback rules and minimum evidence packet requirements for Nanobot Graphify/standing-worker results.


### 2026-07-04 P1.3 dashboard source validation

Result: green source-level dashboard validation; no live vault publication or mutation.

Changes:
- Added `validate-source` mode to `tools/obsidian_review_dashboard.py`.
- Added `make dashboard-validate` to write JSON and Markdown validation reports under `out/reports/dashboard-source-validate/`.
- Added regression tests for dashboard source constraints and pending proposal filtering.

Evidence:
- `python3 -m pytest tests/test_review_dashboard.py -q` passed.
- `make dashboard-validate` passed and reported `status: ok`, `checklist_items: 6`, no findings.

Safety:
- The dashboard remains proposal-only source material.
- Publishing into the live vault still requires manual copy by Дмитрий or the approved obslayer apply gate.


### 2026-07-04 P2 final468 Graphify semantic acceptance

Result: full Graphify-derived sandbox semantic pass accepted; this supersedes the older “medium/full sandbox probe pending” backlog item for the current handoff set.

Evidence:
- `out/reports/graphify-final468-acceptance-20260704T065729Z/REPORT.md`
- `out/reports/graphify-embedding-runs/step468-final-safe-20260703T192852Z/embedding-run.json`
- `out/reports/graphify-embedding-query-smoke/final468-20260704T065635Z/query-smoke.json`

Counts:
- records `468`, processed `467`, skipped `1` empty file;
- embedding sidecars `467`;
- query-smoke chunks `3605`;
- missing embeddings `0`.

Boundary:
- sandbox/derived-cache/query only;
- no live vault mutation;
- no routine unattended production indexing;
- safe-batch mode is required on this 4 GB VPS.


### 2026-07-04 P3 semantic query proposal-only report

Result: first repeatable proposal-only report generated from the accepted final468 semantic query-smoke evidence.

Changes:
- Added `tools/obsidian_semantic_proposal_report.py`.
- Added `make semantic-proposal-report`.
- The report normalizes query-smoke hits into review candidates while keeping `targets: []`, `risk_class: read_only_only`, `dry_run_default: true`, and `live_mutation_authorized: false`.

Evidence:
- Targeted tests: `pytest tests/test_semantic_proposal_report.py -q` passed.
- Real final468 proposal-only report: `out/proposals/semantic-query-reports/final468-operator-review-20260704T093433Z/REPORT.md`.
- Source query evidence: `out/reports/graphify-embedding-query-smoke/final468-20260704T065635Z/query-smoke.json`.

Boundary:
- candidate review only; no proposed file edits; no live vault mutation; no approval manifest generated.


### 2026-07-04 P3 semantic proposal explanation UX

Result: dashboard/explain now understands semantic query proposal-only reports.

Changes:
- `tools/obsidian_review_dashboard.py explain` renders semantic candidate count, top candidates, query intents, and safety boundary.
- Empty-target proposal-only reports now show approval phrase as `not applicable — proposal-only / no targets` instead of `None`.
- Regression test added in `tests/test_review_dashboard.py`.

Evidence:
- `pytest tests/test_review_dashboard.py -q` passed.
- `make verify` passed.
- Generated explanation: `out/proposals/semantic-query-reports/final468-operator-review-20260704T093433Z/EXPLANATION.md`.

Boundary:
- review UX only;
- no live vault mutation;
- no approval manifest generated;
- semantic candidates remain review inputs, not edit targets.


### 2026-07-04 P3 semantic proposal explanation CLI hardening

Result: dashboard/explain remains read-only but is easier and safer to use from operator handoffs.

Changes:
- `tools/obsidian_review_dashboard.py explain` accepts a positional `proposal.json` path as shorthand for `--proposal`.
- Semantic candidate Markdown table cells escape pipe delimiters in paths, queries, scores, and chunks.
- Regression tests cover positional CLI invocation and table escaping.

Evidence:
- `pytest tests/test_review_dashboard.py -q` passed.
- `make verify` passed.

Boundary:
- CLI/report UX only;
- no live vault mutation;
- no approval manifest generated;
- semantic candidates remain review inputs, not edit targets.

### 2026-07-04 P2c Nanobot local scout approval

Result: Дмитрий approved one supervised Nanobot cron for Obsidian Operating Layer maintenance.

Accepted scope:
- initially daily Hermes cron, later explicitly expanded to `every 15m`, local delivery only;
- script: `/home/hermesadmin/.hermes/scripts/nanobot_obslayer_scout.py`;
- script smoke: `--dry-run` verifies preflight/project-state/docs-lag without calling Nanobot/LLM;
- audit model config: `NANOBOT_CONFIG=/home/hermesadmin/.nanobot-hermes/config.audit.json`, preset `codex-small` / `gpt-5.4-mini`;
- output: `out/reports/nanobot-cron-scout/`;
- Nanobot uses the accepted Headroom backend Codex bridge wrapper;
- evidence reads use only the read-only evidence gateway.

Boundary:
- report-only/proposal-only scout;
- no live vault mutation;
- no repository mutation by Nanobot;
- no auth/profile/service/network/deploy/embedding actions;
- any additional cron, delivery change, or scope expansion beyond the approved 15-minute audit requires separate explicit approval.

### 2026-07-04 P3 semantic candidate decision packet

Result: added the next proposal-only step after semantic candidate discovery.

Implemented:

- Added `tools/obsidian_semantic_candidate_decision_packet.py`.
- Added `make semantic-candidate-decision-packet`.
- Added tests in `tests/test_semantic_candidate_decision_packet.py`.
- Generated an operator decision packet from the final468 semantic proposal report.

Boundary:

- decision packet only; no edit targets; no approval manifest; no live vault mutation; no Nanobot/repo mutation by worker.
- promotion means a later targeted proposal may be drafted and reviewed separately.
- first recommended promotion group is link hygiene reports; Nanobot orchestration remains repo/spec-kit follow-up only.

### 2026-07-04 P3 targeted semantic proposal packet

Result: added the next proposal-only promotion step for the `link_hygiene_reports` decision group.

Artifacts/code:

- `src/obslayer/semantic_targeted_proposal.py`
- `tools/obsidian_semantic_targeted_proposal.py`
- `tests/test_semantic_targeted_proposal.py`
- `make semantic-targeted-proposal`

Safety boundary:

- proposal-only targeted packet; no edit targets; no approval manifest; no live vault mutation; no backups.
- first promoted group remains `link_hygiene_reports`; exact documentation/edit targets must be selected in a later operator-reviewed diff proposal.


### 2026-07-04 P3 LLM channel smoke and semantic workflow discoverability

Result: acted on Nanobot scout followups without mutating the live vault.

Added:

- `docs/spec-kit/schemas/llm-channel.schema.json` for secret-free LLM channel smoke artifacts.
- `tools/obsidian_llm_channel_smoke.py` and `src/obslayer/llm_channel_smoke.py`.
- `make llm-channel-smoke` and `make llm-channel-smoke-live`.
- `docs/spec-kit/29-semantic-proposal-workflow.md` as the standalone proposal-only semantic workflow spec.

Boundary:

- Smoke asserts route shape and probes only local Headroom/evidence-gateway health when `--live-probes` is requested.
- No repo/vault/auth/profile/service mutation by Nanobot.
- Alternate Nanobot HTTP bridge guesses are not accepted operating paths.


### 2026-07-04 P3 targeted semantic proposal explanation

Result: dashboard/explain now understands targeted semantic proposal packets.

Changed:

- `tools/obsidian_review_dashboard.py explain` accepts proposal-only semantic targeted packets with empty targets and `live_mutation_authorized: false`.
- The explanation renders candidate source paths, proposed review actions, and source decision packet.
- Added regression coverage for generated link-hygiene targeted proposal artifacts.

Boundary:

- candidate paths remain evidence inputs, not edit targets; no approval manifest; no live vault mutation.


### 2026-07-04 P3 semantic review index

Result: added the first review/index artifact after targeted semantic proposal packets.

Changed:

- Added `src/obslayer/semantic_review_index.py`.
- Added `tools/obsidian_semantic_review_index.py`.
- Added `tests/test_semantic_review_index.py`.
- Added `make semantic-review-index`.

Boundary:

- review index only; candidate paths are evidence inputs; no live vault mutation; no approval manifest; no edit targets.


### 2026-07-04 P2c Nanobot 15-minute audit loop

Result: existing Nanobot scout cron `212b7e8f3c21` was updated to a bounded 15-minute local audit loop after explicit user request.

Changed runtime:

- schedule: `every 15m`;
- script: `/home/hermesadmin/.hermes/scripts/nanobot_obslayer_scout.py`;
- mode: no-agent script, local delivery only;
- outputs: `out/reports/nanobot-cron-scout/`;
- script now writes `project-state.json`, uses a lock to prevent overlap, keeps timeout/block reporting, and asks Nanobot to check whether project/docs lag behind latest commits/proposals/reports.

Boundary:

- read-only/proposal-only audit; no live vault mutation; no repo mutation by Nanobot; no auth/profile/service/network/deploy/embedding changes; blocked reports are acceptable when provider capacity is unavailable.


### 2026-07-04 P2c deterministic docs lag audit

Result: added a local structural audit that checks whether key docs/specs mention the current accepted Nanobot, channel, and semantic workflow markers.

Changed:

- Added `src/obslayer/project_docs_lag_audit.py`.
- Added `tools/obsidian_project_docs_lag_audit.py`.
- Added `tests/test_project_docs_lag_audit.py`.
- Added `make project-docs-lag-audit`.

Boundary:

- read-only docs marker audit; no live vault mutation; no LLM required; intended as deterministic companion evidence for the 15-minute Nanobot audit scout.
- 2026-07-04 follow-up: live gateway service restarted after explicit approval; `/snapshot.json` and `--dry-run` script preflight verified.

### 2026-07-04 P1/P2c orchestrator consolidation spec

Result: active operating rules were consolidated into one operator-facing spec without deleting the source specs.

Changed:
- Added `docs/spec-kit/30-orchestrator-operating-spec.md` as the first-read orchestration document.
- Updated `docs/spec-kit/00-overview.md` to list the consolidated spec.

Boundary:
- This is docs-only.
- Live vault mutation remains forbidden without explicit approval manifest.
- Nanobot remains proposal-only and supervised by Hermes.

Runtime note:
- Manual Nanobot scout was launched; deterministic docs-lag audit reported `ok`.
- Initial Nanobot Codex backend review was blocked by `HTTP 401`; after Codex device login and per-run Codex auth inheritance check, the scout completed successfully at `out/reports/nanobot-cron-scout/20260704T152408Z/REPORT.md` with verdict `current`.

Follow-up from Nanobot scout:
- keep a generated-artifact pointer section in `30-orchestrator-operating-spec.md` and `docs/acceptance/index.md`;
- keep gateway evidence URL traversal explicit via `/snapshot.json`;
- treat Nanobot as second opinion, with deterministic docs-lag audit as companion evidence.

### 2026-07-04 Orchestrator semantic decision packet

Result: proposal-only operator decision packet created for the current semantic/link-hygiene findings.

Decision:
- Promote `link_hygiene_reports` to the next proposal-only evidence brief/review-index refresh.
- Promote `nanobot_orchestration_context` only as a repo spec-kit follow-up checklist.
- Keep `approval_safety_context` as guardrail evidence.
- Keep `graphify_context` as roadmap/context evidence.

Evidence:
- Operator decision packet: `out/proposals/operator-decision-packets/link-hygiene-20260704T153221Z/REPORT.md`
- Source review index: `out/proposals/semantic-review-indexes/link-hygiene-20260704T1200Z/REPORT.md`
- Nanobot scout second opinion: `out/reports/nanobot-cron-scout/20260704T152408Z/REPORT.md`

Safety:
- Proposal-only/read-only.
- `live_mutation_authorized: false`.
- No approval manifest created.
- No live vault targets selected.

Next safe slice:
- Create the link-hygiene evidence brief with `targets_empty: true`, classifying old report noise vs current signal before any future target-diff proposal.

### 2026-07-04 Link hygiene evidence brief

Result: proposal-only link-hygiene evidence brief created after reading the 8 semantic review-index items and running a fresh read-only live-vault signal check.

Evidence:
- Link hygiene evidence brief: `out/proposals/link-hygiene-evidence-briefs/20260704T154000Z/REPORT.md`
- Fresh read-only current scan: `out/reports/link-hygiene-current-scan/20260704T-current-brief/REPORT.md`
- Source operator decision packet: `out/proposals/operator-decision-packets/link-hygiene-20260704T153221Z/REPORT.md`

Decision:
- Historical link-hygiene reports confirm a persistent link-debt signal, but the old samples are report-heavy and partly Soul/policy-sensitive.
- The next safe target class is a fresh `non-report working-note wikilink triage report`, proposal-only first.
- Do not directly edit links from old report samples.
- Do not auto-archive duplicates or touch Soul-adjacent material without a separate policy decision.

Safety:
- Proposal-only/read-only.
- `live_mutation_authorized: false`.
- `targets_empty: true`.
- No approval manifest created.
- Generated artifacts only under `out/`.

Next safe slice:
- Generate the non-report working-note wikilink triage report with examples/classes only and no edit targets.

### 2026-07-04 Non-report working-note wikilink triage

Result: fresh proposal-only triage generated for current wikilink debt outside generated reports.

Evidence:
- Triage report: `out/proposals/non-report-working-note-wikilink-triage/20260704T154634Z/REPORT.md`
- Machine-readable triage: `out/proposals/non-report-working-note-wikilink-triage/20260704T154634Z/triage.json`
- Docs lag audit: `out/reports/project-docs-lag-audit/orchestrator-20260704T-working-note-triage/REPORT.md`
- Channel registry verify: `out/reports/channel-registry-verify/orchestrator-20260704T-working-note-triage/REPORT.md`
- Source evidence brief: `out/proposals/link-hygiene-evidence-briefs/20260704T154000Z/REPORT.md`

Observed signal:
- `markdown_files_scanned`: `538`
- `total_issues`: `6126`
- `non_report_issues`: `389`
- `working_note_issues_excluding_reports_and_soul_policy_sensitive`: `105`
- `soul_or_policy_sensitive_issues_report_only`: `284`
- `report_or_generated_issues`: `5737`

Decision:
- Promote only non-sensitive working-note clusters to the next proposal slice.
- Keep report/generated and Soul/policy-sensitive findings as evidence only.
- Do not mutate live vault from triage samples.

Safety:
- Proposal-only/read-only.
- `live_mutation_authorized: false`.
- `targets_empty: true`.
- No approval manifest created.
- Generated artifacts only under `out/`.

Next safe slice:
- Draft a targeted proposal for non-sensitive working-note clusters with exact candidate files/targets, still without apply.

### 2026-07-04 Working-note link targeted proposal

Result: targeted proposal-only candidate set created from the 105 non-sensitive working-note ambiguous wikilinks.

Evidence:
- Targeted proposal report: `out/proposals/working-note-link-targeted-proposals/20260704T155803Z/REPORT.md`
- Machine-readable proposal: `out/proposals/working-note-link-targeted-proposals/20260704T155803Z/proposal.json`
- Docs lag audit: `out/reports/project-docs-lag-audit/orchestrator-20260704T-working-note-targeted/REPORT.md`
- Channel registry verify: `out/reports/channel-registry-verify/orchestrator-20260704T-working-note-targeted/REPORT.md`
- Source triage: `out/proposals/non-report-working-note-wikilink-triage/20260704T154634Z/REPORT.md`

Observed signal:
- `observed_working_ambiguous_records`: `105`
- `candidate_rewrites`: `102`
- `held_for_human_review`: `3`
- `candidate_files`: `26`

Decision:
- Candidate rewrites are same top-level vault-root disambiguations, mainly `Memory-Vault/...` links avoiding ambiguous `Soul-Vault/...` duplicates.
- Hold the 3 records with no single same-root target for human/domain review.
- Do not apply yet; next step is operator review and, if approved later, an explicit approval manifest with backups.

Safety:
- Proposal-only artifact under `out/`.
- `live_mutation_authorized: false`.
- `approval_manifest_created: false`.
- Report/generated and Soul/policy-sensitive files excluded from candidate targets.

Next safe slice:
- Run an operator review pass over the 102 proposed rewrites and split them into approve/hold/reject groups before any approval manifest.

### 2026-07-04 Working-note link operator review

Result: operator review pass completed for the 102 targeted working-note disambiguation candidates.

Evidence:
- Operator review report: `out/proposals/working-note-link-operator-reviews/20260704T161938Z/REPORT.md`
- Machine-readable review: `out/proposals/working-note-link-operator-reviews/20260704T161938Z/review.json`
- Source targeted proposal: `out/proposals/working-note-link-targeted-proposals/20260704T155803Z/REPORT.md`
- Docs lag audit: `out/reports/project-docs-lag-audit/orchestrator-20260704T-operator-review-final/REPORT.md`
- Channel registry verify: `out/reports/channel-registry-verify/orchestrator-20260704T-operator-review-final/REPORT.md`

Observed decision split:
- `reviewed_candidates`: `102`
- `approved_for_manifest_candidate`: `102`
- `held_for_human_or_rule_review`: `3`
- `rejected`: `0`
- `approved_source_files`: `26`

Decision:
- Approve the 102 same-root working-note disambiguations only as manifest candidates.
- Keep the 3 inherited held records out of any automated apply path until a human/domain rule resolves them.
- Do not create an approval manifest or apply edits from this review without Dmitry's explicit named approval.

Safety:
- Proposal/review-only artifact under `out/`.
- `live_mutation_authorized: false`.
- `approval_manifest_created: false`.
- No live vault files edited.

Next safe slice:
- Prepare a manifest-candidate/dry-run packet for the 102 approved rewrites, still without live apply, or request explicit live-apply authorization before creating a real approval manifest.

### 2026-07-04 Working-note link manifest-candidate dry-run

Result: manifest-candidate/dry-run packet prepared from the approved operator review set, without creating an approval manifest or mutating the live vault.

Evidence:
- Dry-run packet report: `out/proposals/working-note-link-manifest-candidates/20260704T162439Z/REPORT.md`
- Machine-readable packet: `out/proposals/working-note-link-manifest-candidates/20260704T162439Z/manifest-candidate.json`
- Diff previews: `out/proposals/working-note-link-manifest-candidates/20260704T162439Z/diffs/`
- Source operator review: `out/proposals/working-note-link-operator-reviews/20260704T161938Z/REPORT.md`

Observed dry-run set:
- `approved_rewrite_entries`: `102`
- `target_files`: `26`
- `dry_run_replacements`: `102`
- `held_items_excluded`: `3`

Decision:
- Treat this packet as the current named candidate for future approval review.
- It is not an approval manifest and does not authorize apply.
- The 3 held items remain excluded from this change set.

Safety:
- Dry-run/proposal-only artifact under `out/`.
- `live_mutation_authorized: false`.
- `approval_manifest_created: false`.
- `live_apply_performed: false`.
- No backups were created because no live apply was attempted.

Next gate:
- If Dmitry explicitly approves this named packet, create a real approval manifest that binds target vault, packet path, target files, expected hashes, backup root, and change set; then backup, apply, and verify.

### 2026-07-04 Working-note link live apply

Result: Dmitry explicitly approved the named manifest-candidate packet and the 102 approved working-note wikilink disambiguations were applied to the live vault.

Approval and evidence:
- Approval manifest: `out/approval-manifests/working-note-link-apply/20260704T163336Z/approval-manifest.json`
- Apply report: `out/reports/working-note-link-apply/20260704T163336Z/REPORT.md`
- Apply result JSON: `out/reports/working-note-link-apply/20260704T163336Z/apply-result.json`
- Post-apply verification: `out/reports/working-note-link-post-apply-verify/20260704T163336Z/REPORT.md`
- Docs lag audit: `out/reports/project-docs-lag-audit/orchestrator-20260704T-live-apply/REPORT.md`
- Channel registry verify: `out/reports/channel-registry-verify/orchestrator-20260704T-live-apply/REPORT.md`
- Source dry-run packet: `out/proposals/working-note-link-manifest-candidates/20260704T162439Z/manifest-candidate.json`

Applied set:
- `target_files`: `26`
- `replacements`: `102`
- `backups`: `26`
- `held_items_excluded`: `3`

Safety and verification:
- Backups created before writes under `/home/hermesadmin/Obsidian/_Backups/obsidian-operating-layer/20260704T163336Z`.
- Apply was limited to files listed in the approval manifest.
- Post-apply verification result: `ok`; `out/reports/working-note-link-post-apply-verify/20260704T163336Z/REPORT.md` reports `old_remaining: 0` and `issues: 0`.
- The 3 held/domain-review items were not applied.

Next safe slice:
- Run a fresh post-apply link-hygiene observation and compare the working-note ambiguous count against the pre-apply packet.

### 2026-07-04 Working-note link post-apply observation

Result: fresh observation completed after the approved live apply.

Evidence:
- Observation report: `out/reports/working-note-link-post-apply-observation/20260704T164100Z/REPORT.md`
- Machine-readable observation: `out/reports/working-note-link-post-apply-observation/20260704T164100Z/observation.json`
- Source post-apply verify: `out/reports/working-note-link-post-apply-verify/20260704T163336Z/REPORT.md`

Observed state:
- `target_files_observed`: `26`
- `approved_old_remaining`: `0`
- `approved_new_present_at_least`: `110`
- `held_excluded_items`: `3`
- `held_raw_links_still_present`: `3`
- `held_missing_unexpected`: `0`
- `target_file_simple_broken_wikilinks_after`: `0`

Decision:
- Close the approved apply set as successfully applied and observed.
- Keep the 3 held report/README links out of the apply path.
- Remaining ambiguity signal still exists and should be handled by a new triage slice, not by extending this approved apply.

Next safe slice:
- Run full non-report working-note triage again against the post-apply vault state and quantify remaining actionable link debt.

### 2026-07-04 Held Reports README link apply

Result: the 3 previously held `Reports/.../README` links were resolved with an explicit domain rule and applied to the live vault.

Domain rule:
- For sources under `Memory-Vault/Hermes/*`, `Reports/.../README` resolves to `Memory-Vault/Hermes/Reports/.../README`.

Evidence:
- Mini-proposal: `out/proposals/working-note-held-report-readme-fixes/20260704T165250Z/REPORT.md`
- Approval manifest: `out/approval-manifests/working-note-held-report-readme-apply/20260704T165519Z/approval-manifest.json`
- Apply report: `out/reports/working-note-held-report-readme-apply/20260704T165519Z/REPORT.md`
- Apply result JSON: `out/reports/working-note-held-report-readme-apply/20260704T165519Z/apply-result.json`

Applied set:
- `target_files`: `3`
- `replacements`: `3`
- `backups`: `3`
- `issues`: `0`

Safety and verification:
- Backups created before writes under `/home/hermesadmin/Obsidian/_Backups/obsidian-operating-layer/20260704T165519Z`.
- Apply was limited to the 3 approved source files.
- Post-apply verification result: `ok`.

Search note:
- Graph links now point explicitly to `Memory-Vault/Hermes/Reports/graphify-spark-corpus-c10-2026-06-27/README`, so graph traversal and future hybrid retrieval can resolve them deterministically.

### 2026-07-04 Post-held working-note link triage and next proposal

Result: after the 3 held report README links were applied, Hermes ran a fresh read-only working-note triage and prepared the next proposal-only disambiguation packet. No live vault edits were performed in this slice.

Evidence:
- Fresh triage report: `out/reports/non-report-working-note-wikilink-post-held-triage/20260704T170534Z/REPORT.md`
- Fresh triage JSON: `out/reports/non-report-working-note-wikilink-post-held-triage/20260704T170534Z/triage.json`
- Next safe proposal: `out/proposals/working-note-link-next-safe-disambiguation/20260704T170712Z/REPORT.md`
- Proposal JSON: `out/proposals/working-note-link-next-safe-disambiguation/20260704T170712Z/proposal.json`

Observed state:
- `markdown_files_scanned`: `706`
- `working_note_issues_excluding_reports_and_soul_policy_sensitive`: `286`
- `report_readme_leftovers`: `0`
- `candidate_rewrites`: `231`
- `candidate_files`: `41`
- `held_for_review`: `55`

Decision:
- Treat this as a new proposal-only packet, not an extension of the prior approval.
- Do not apply without a named approval manifest and explicit Dmitry approval.
- Held items include occurrence-count duplicates and targets without a safe same-project candidate; keep them out of the next apply unless a narrower rule is reviewed.

Next safe slice:
- Operator-review the 231 candidate rewrites and, only if approved by Dmitry, build a dry-run manifest candidate for those candidates.
### 2026-07-04 Agentic OS operator flow / review queue spec

Result: added an explicit proposal-only operator flow and evidence-gated review queue state machine.

Changed:
- Added `docs/spec-kit/31-operator-flow-and-review-queue.md`.
- Updated `docs/spec-kit/00-overview.md`, `docs/spec-kit/30-orchestrator-operating-spec.md`, and `docs/acceptance/index.md` to point at it.

Purpose:
- Make intake -> evidence -> route -> proposal -> review -> approval gate explicit.
- Give Nanobot/Hermes a shared Agentic OS coordination surface without granting Nanobot live mutation rights.
- Add the first deterministic queue-index generator under `tools/obsidian_operator_review_queue.py`, emitting `out/reports/operator-review-queue/<timestamp>/queue.json` and `REPORT.md`.

Evidence:
- `pytest tests/test_operator_review_queue.py -q` passed.
- Generated queue index: `out/reports/operator-review-queue/20260704T-agentic-flow/REPORT.md`.

Safety:
- Repo docs + deterministic local tool/test change; generated artifacts only under `out/`.
- `live_mutation_authorized: false`.
- No approval manifest created.
- No live vault/service/auth/cron mutation.
### 2026-07-04 Codex ⇄ Hermes communication channel

Result: added a local task/report/ACK channel for Codex as bounded implementation/review worker.

Changed:
- Added `docs/spec-kit/32-codex-hermes-communication-channel.md`.
- Added canonical helper `tools/codex_hermes_comm.py` and wrapper `/home/hermesadmin/.hermes/scripts/codex_hermes_comm.py`.
- Added tests in `tests/test_codex_hermes_comm.py`.
- Added role policy files under `~/.codex-hermes/docs/ROLE_POLICY.json` and `.md`.
- Updated AGENTS, channel registry, acceptance index, and orchestrator specs.

Boundary:
- Local/server-side task/report files only.
- No Codex cron installed by default; durable watcher requires explicit user approval.
- Repo writes are task-scoped only; review tasks are read-only.
- Live vault/auth/profile/service/deploy/cron/network/public/paid actions remain gated by explicit approval.

Evidence:
- `python3 tools/codex_hermes_comm.py selftest` returned `status: ok`.
- Synthetic task/report/watch E2E passed with Hermes ACK.
- Codex review was attempted in read-only mode; Codex reported environment sandbox read failure and recommended keeping channel code/policy inside the repo plus adding self-test. Both recommendations were applied.


## Codex native runtime

Codex is made repo-native through `docs/spec-kit/33-codex-native-runtime.md`, `/home/hermesadmin/.codex-hermes/bin/hermes-codex-run`, schema-versioned task/report packets, and explicit separation from Nanobot's architecture scout channel. Nanobot may recommend Codex tasks; Hermes dispatches and accepts them.
