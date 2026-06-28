# Next Improvements Roadmap

## Purpose

This document is the missing improvement-oriented spec after the MVP baseline. It complements `12-full-functional-and-diagram-test-plan.md`, which verifies the current system, by defining what to improve next and how to accept each improvement.

## Baseline already delivered

Current GitHub baseline provides:

- read-only / dry-run safety flow: `observe -> propose -> verify -> apply dry-run`;
- proposal normalization with protected-path refusal;
- sandbox vault harness;
- read/search/analyze/render adapter contracts;
- diagram/PDF proof-of-concept from committed Mermaid sources;
- Obsidian review-dashboard source docs;
- controlled-autonomy queue for observe/index/report jobs;
- regression tests for the field-run gaps found so far.

This is usable as a safety-first MVP, not as full autonomous production.

## Gap corrected by this spec

The previous follow-up work focused on testing and baseline verification. That was useful but incomplete: it did not turn the roadmap into a prioritized improvement batch for daily use.

This document defines that next improvement batch.

## Improvement principles

1. Keep ready components first; local code is glue, policy, and acceptance.
2. Expand autonomy only after field evidence, not by assumption.
3. Live vault mutation remains behind explicit approval manifest, backup, and verify.
4. Every improvement must produce a user-visible artifact or a measurable safety/UX gain.
5. Generated artifacts stay under `out/`; committed specs/tests live under `docs/` and `tests/`.

## P0 — safety and correctness improvements

### P0.1 Proposal worker malformed-input hardening

Status: partially implemented by regression tests.

Acceptance:

- string targets are refused with clear issues;
- targets without `path` are refused;
- targets without replacement payload are refused;
- non-list `findings` are refused;
- mixed/conflicting target sets produce deterministic refusal.

Verification:

```bash
pytest tests/test_proposal_normalization.py
```

### P0.2 Controlled-autonomy report format clarity

Status: implemented and regression-tested.

Problem found during field run: `controlled_autonomy report --out file.json` writes Markdown unless `--json-out` is supplied.

Acceptance:

- CLI help and docs make Markdown vs JSON outputs explicit;
- tests cover `--out` Markdown and `--json-out` JSON simultaneously;
- no command example implies that `--out *.json` creates JSON.

Verification:

```bash
pytest tests/test_controlled_autonomy.py
python3 tools/obsidian_controlled_autonomy.py report --help
```

### P0.3 Apply rehearsal only on disposable sandbox

Status: implemented as a regression-tested disposable sandbox rehearsal.

Acceptance:

- create a disposable sandbox vault;
- create a narrow proposal and approval manifest for the sandbox only;
- run live apply against the sandbox, not the real vault;
- verify backup and fresh observation after apply;
- document rollback evidence.

Verification target:

- report under `out/reports/apply-rehearsal-*` for manual runs;
- regression test `tests/test_apply_rehearsal.py` verifies backup and post-observe evidence;
- no changes under `/home/hermesadmin/Obsidian`.

## P1 — daily-use UX improvements

### P1.1 Pending proposals command

Status: implemented via `tools/obsidian_review_dashboard.py list` and regression-tested.

Goal: one command to list proposals that need human review.

Acceptance:

- prints proposal id, source, risk, target count, status, and report path;
- supports JSON output for dashboard use;
- does not read secrets or mutate vault.

Command:

```bash
python3 tools/obsidian_review_dashboard.py list --proposal-root out/proposals --json
```

### P1.2 Human explanation for a proposal

Status: implemented via `tools/obsidian_review_dashboard.py explain` and regression-tested.

Goal: explain a proposal in Telegram/Obsidian-friendly language.

Acceptance:

- summarizes what will change, why, risk, rollback, and exact approval phrase;
- includes evidence links/paths;
- refuses explanation if proposal is malformed or unsafe.

### P1.3 Dashboard field review

Goal: validate that the dashboard is useful inside Obsidian, not only as markdown files.

Acceptance:

- open `docs/obsidian-review-dashboard/index.md` in Obsidian or a copied dashboard vault;
- Dataview/Templater-facing sections are readable;
- status labels work: `proposed`, `needs-review`, `applied`, `rejected`;
- manual checklist covers safety boundary, paths, evidence, and verify result.

### P1.4 Diagram readability pass

Goal: make diagrams useful for planning and user communication.

Acceptance:

- PDF/SVG visual review completed;
- architecture, worker flow, and safety sequence are understandable without reading code;
- any confusing labels are fixed in `docs/diagrams/*.mmd`;
- generated PDF path is recorded.

## P2 — capability expansion

### P2.1 Real field-test slice

Status: implemented as proposal-only CLI flow via `tools/obsidian_field_slice.py` and regression-tested on a disposable vault subset.

Goal: run one small real scenario end-to-end without live mutation.

Flow:

```text
observe -> finding/proposal -> dashboard review -> reject/approve decision record
```

Acceptance:

- uses a small approved vault subset or sandbox copy;
- produces proposal bundle and review note;
- decision is recorded as reject/approve/pending;
- no live apply unless separately approved.

Command:

```bash
python3 tools/obsidian_field_slice.py --vault /tmp/approved-vault-subset --out-root out/field-slices/example --decision pending
```

### P2.2 RAG/graph candidate benchmark

Goal: test the primary ready RAG/graph candidate against a copied vault benchmark.

Acceptance:

- install/run only inside sandbox;
- fixed queries produce parseable findings;
- findings normalize into proposal-worker schema;
- resource cost and quality are recorded.

### P2.3 MCP read-only adapter expansion

Goal: expand read/search/graph evidence collection without write tools.

Acceptance:

- dangerous tool calls are refused;
- read/search returns evidence with source paths;
- any write-like intent is converted to proposal, not applied.

## P3 — polish and operations

- Better report templates for Telegram summaries.
- A compact `how to use` operator guide.
- Cleaner command aliases for common flows.
- Scheduled observe/index reports after explicit cron approval.
- More visual themes for diagrams.

## Proposed next kanban batch

1. `p0_controlled_autonomy_report_format_docs_tests`
2. `p0_sandbox_apply_rehearsal`
3. `p1_pending_proposals_command`
4. `p1_dashboard_manual_review`
5. `p1_diagram_readability_acceptance`
6. `p2_field_test_slice_no_live_apply`

The remaining manual/UI and adapter benchmark contracts are defined in
`15-manual-and-adapter-acceptance.md`.

## Done criteria for this roadmap

The roadmap is considered executed only when:

- P0 items are implemented and verified;
- at least one P1 daily-use UX flow is usable by Дмитрий;
- one P2 field slice has produced a real proposal/review artifact;
- all evidence is linked from `14-operational-acceptance-report.md` and
  `15-manual-and-adapter-acceptance.md`;
- GitHub is clean and synchronized.

## Stop conditions

Stop and ask Дмитрий before:

- live writes to the real vault;
- destructive delete/move/merge;
- production deploy/restart/network exposure;
- paid/high-volume API use;
- secrets or browser profile handling;
- durable Soul/governance edits.
