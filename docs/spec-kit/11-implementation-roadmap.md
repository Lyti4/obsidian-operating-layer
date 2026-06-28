# Implementation Roadmap

## Goal

Turn the final desired architecture into working, sandbox-verified increments.

## Phase 0 — current baseline

Already present:

- obslayer safety core;
- dry-run default;
- approval manifest requirement;
- protected path refusal;
- backup and verify flow;
- initial component inventory;
- final desired architecture spec.

## Phase 1 — contracts and schemas

Deliverables:

- `06-adapter-contracts.md` accepted;
- `07-local-queue-schema.md` accepted;
- JSON schema files for adapter and task records;
- sample adapter records for MCP/RAG/diagram candidates.

Verification:

- schema validates sample records;
- direct-write capability cannot pass accepted adapter policy.

## Phase 2 — sandbox vault harness

Deliverables:

- create copied test vault under `out/sandbox-vaults/`;
- script to create/reset sandbox from small approved source subset;
- protected paths excluded by default.

Verification:

- sandbox creation does not mutate live vault;
- file count and excluded paths are reported.

## Phase 3 — read-only MCP adapter

Deliverables:

- evaluate primary MCP candidate in sandbox;
- wrapper exposes read/search/graph only;
- write-like calls are refused or converted to proposal.

Verification:

- read/search returns expected evidence;
- attempted direct write does not change sandbox/live vault unless explicit sandbox-only test.

## Phase 4 — RAG/graph adapter

Deliverables:

- evaluate Kwipu or closest ready Graph RAG candidate;
- produce related notes/backlinks/orphans/MOC candidates;
- normalize output to finding schema.

Verification:

- fixed test queries produce parseable findings;
- no live writes.

## Phase 5 — diagram/PDF proof-of-concept

Deliverables:

- source diagrams under `docs/diagrams/`;
- generated outputs under `out/diagrams/` and `out/reports/`;
- first architecture PDF for Дмитрий.

Verification:

- PDF generated from source;
- generation command recorded;
- no sensitive content exposed.

## Phase 6 — proposal normalization

Deliverables:

- `proposal-worker` converts findings into obslayer proposal format;
- proposals include evidence, risk, target list, and no protected paths.

Verification:

- proposal passes existing safety validation;
- unsafe target test is refused.

## Phase 7 — Obsidian review dashboard

Deliverables:

- Dataview/Templater-friendly review notes;
- task/proposal/report index;
- status labels: proposed/applied/rejected/needs-review.

Verification:

- dashboard can be opened in Obsidian;
- automated writes to dashboard still use safety gate unless manual.

## Phase 8 — controlled autonomy

Deliverables:

- scheduled observe/index/report only;
- no auto live mutation except explicitly approved safe report/index paths;
- periodic acceptance report.

Verification:

- background jobs are tracked and cleaned up;
- reports distinguish applied vs proposed.

## Stop conditions

Stop and ask Дмитрий before:

- production deploy/restart/network exposure;
- destructive delete/move/merge;
- paid services/high-volume API use;
- secrets/credentials handling;
- Soul-governance policy edits beyond explicit requested text.
