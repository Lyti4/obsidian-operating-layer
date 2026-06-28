# Operational Acceptance Report

## Purpose

This report closes the first operational-acceptance pass after the MVP baseline and `13-next-improvements-roadmap.md`. It records what was implemented, what was verified by commands, and what still requires explicit human/UI review.

## Scope

Acceptance scope covered in this pass:

- proposal-only field slice;
- pending proposal listing;
- human-readable proposal explanation;
- disposable sandbox apply rehearsal;
- controlled-autonomy report format clarity;
- diagram/PDF generation and server-side visual acceptance;
- dashboard static and server-side usability acceptance.

The real live vault was not mutated. Live apply to `/home/hermesadmin/Obsidian` remains outside this acceptance pass.

## Delivered acceptance items

### P0.2 Controlled-autonomy report format clarity

Status: accepted.

Evidence:

- `tools/obsidian_controlled_autonomy.py report --help` documents that `--out` writes Markdown and `--json-out` writes JSON.
- `tests/test_controlled_autonomy.py` covers both outputs in one run.

Acceptance result:

- Markdown and JSON report formats are no longer ambiguous.

### P0.3 Disposable sandbox apply rehearsal

Status: accepted.

Evidence:

- `tests/test_apply_rehearsal.py` creates a disposable vault in a test temp directory.
- The test creates a narrow proposal and approval manifest.
- Live apply is executed only against the disposable sandbox vault.
- Backup and post-observe evidence are verified.

Acceptance result:

- Apply semantics are rehearsed without touching the real vault.

### P1.1 Pending proposals command

Status: accepted.

Command:

```bash
python3 tools/obsidian_review_dashboard.py list --proposal-root out/proposals --json
```

Evidence:

- `tests/test_review_dashboard_cli.py` verifies JSON and Markdown list output.
- Applied/rejected proposals are excluded from pending output.

Acceptance result:

- There is a daily-use command to see proposals that need review.

### P1.2 Human explanation for a proposal

Status: accepted.

Command:

```bash
python3 tools/obsidian_review_dashboard.py explain --proposal out/proposals/example/proposal.json
```

Evidence:

- `tests/test_review_dashboard_cli.py` verifies that explanations include risk, target list, approval phrase, summary, and next safe step.
- Unsafe non-dry-run proposals are refused.

Acceptance result:

- Dmitry can ask for a human-readable proposal explanation before any approval/apply decision.

### P1.3 Dashboard field review

Status: accepted by server-side manual review; live Obsidian publication remains gated.

Evidence:

- `docs/obsidian-review-dashboard/index.md` contains Dataview sections for review queue, proposal index, report index, and task index.
- Dashboard empty-state guidance documents expected vault paths and explains that an empty Dataview block is not approval evidence.
- `docs/obsidian-review-dashboard/templates/report-template.md` provides a non-empty acceptance report template with safety/evidence/decision fields.
- Status labels are constrained to `proposed`, `needs-review`, `applied`, and `rejected`.
- `tests/test_phase07_review_dashboard_docs.py` verifies dashboard safety wording and status coverage.

Acceptance result:

- Dashboard source is readable and ready to copy/publish through the normal approval gate; expected vault structure and empty-state behavior are explicit.
- Дмитрий cannot open server-local files directly, so Hermes Agent performed the manual file-level review and recorded the decision in `15-manual-and-adapter-acceptance.md`.

### P1.4 Diagram readability acceptance

Status: accepted by server-side manual review with real Mermaid-rendered SVG artifacts.

Evidence:

- `docs/diagrams/architecture.mmd`
- `docs/diagrams/worker-flow.mmd`
- `docs/diagrams/safety-sequence.mmd`
- Generated SVG/PDF artifacts under `out/diagrams/` and `out/reports/` during acceptance runs.
- `tests/test_diagram_pdf_adapter.py` verifies render-only policy and artifact generation.

Acceptance result:

- Diagrams are reproducible from committed sources and now render as actual Mermaid SVG diagrams, not only source-preview fallbacks.
- Hermes Agent recorded the server-side visual decision in `15-manual-and-adapter-acceptance.md`.

### P2.1 Proposal-only field-test slice

Status: accepted.

Command:

```bash
python3 tools/obsidian_field_slice.py \
  --vault /tmp/approved-vault-subset \
  --out-root out/field-slices/example \
  --decision pending
```

Evidence:

- `tools/obsidian_field_slice.py` implements observe -> finding -> proposal -> verify -> dashboard list -> decision record.
- `tests/test_field_slice.py` verifies the flow on a disposable vault subset.
- Field-slice decisions record `live_apply: not-run` and `mutation_boundary: proposal-only`.

Acceptance result:

- The project has a safe end-to-end proposal-only field scenario.

## Verification commands

Canonical verification for this acceptance state:

```bash
make verify
python3 tools/obsidian_review_dashboard.py list --proposal-root out/proposals --json
python3 tools/obsidian_controlled_autonomy.py report --help
python3 tools/obsidian_field_slice.py --vault /tmp/approved-vault-subset --out-root out/field-slices/example --decision pending
```

Expected canonical result:

- pytest passes;
- ruff passes;
- compileall passes;
- review dashboard list is read-only;
- controlled-autonomy report help clearly separates Markdown and JSON;
- field slice produces proposal/review/decision artifacts without live apply.

## Remaining gaps

### Human/manual acceptance

Server-local dashboard and diagram acceptance is now recorded by Hermes Agent because Dmitry cannot open these files directly. The remaining explicit human decision is:

1. Decide whether any specific real proposal should ever be approved for live apply.

The concrete manual dashboard/diagram review decision is recorded in
`15-manual-and-adapter-acceptance.md`.

### Future capability expansion

These remain future roadmap work, not blockers for the current operational acceptance baseline:

1. Decide whether any specific real proposal should ever be approved for live apply.
2. Scheduled observe/index reports, only after explicit cron approval.
3. Optional additional visual themes for diagrams.

Closed after the original acceptance pass:

- `P2.2` RAG/graph candidate benchmark on sandbox data — implemented and exercised; evidence is recorded in `15-manual-and-adapter-acceptance.md`.
- `P2.3` MCP read-only adapter expansion — implemented and exercised; evidence is recorded in `15-manual-and-adapter-acceptance.md`.
- Better Telegram summary templates — implemented in `docs/telegram-summary-templates.md`.
- Command aliases for common flows — implemented as safe `make` targets.

The sandbox-only benchmark evidence for `P2.2` and `P2.3` is recorded in
`15-manual-and-adapter-acceptance.md`.

## Safety boundary

Accepted live-write boundary:

- real vault: observe/read-only/proposal-only/dry-run;
- disposable sandbox: live apply rehearsal allowed by tests;
- real live apply: explicit approval manifest, exact target binding, backup, and post-verify required.

## Final acceptance decision

Operational acceptance baseline: accepted for field use in safety-first mode.

Use the project for real work as:

```text
observe -> proposal -> dashboard/explain -> human decision -> dry-run/apply gate
```

Do not treat it as unsupervised production autonomy.
