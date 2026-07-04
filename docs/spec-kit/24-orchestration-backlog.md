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
- Historical note: Nanobot was initially tried through `NANOBOT_OPENAI_CODEX_RESPONSES_URL=http://127.0.0.1:8787/v1/responses`; this is no longer the accepted route. Current routing is governed by `28-global-headroom-only-llm-channel.md` and uses the `nanobot-headroom-agent -> /backend-api/codex/responses` bridge.
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
- Generic `/v1/responses` remains a documented anti-pattern for Nanobot Codex bridge work.


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
