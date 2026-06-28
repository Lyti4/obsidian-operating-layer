# Manual and Adapter Acceptance Addendum

## Purpose

This addendum closes the remaining non-code acceptance evidence for `13-next-improvements-roadmap.md` and defines the sandbox-only contracts for the next adapter capability work.

It does not approve live vault mutation. All live-vault usage remains read-only, proposal-only, or dry-run unless a separate approval manifest explicitly authorizes a narrow apply.

## P1.3 Dashboard field review checklist

Status: ready for human/manual Obsidian review.

Source files:

- `docs/obsidian-review-dashboard/index.md`
- `docs/obsidian-review-dashboard/templates/review-note.md`

Manual acceptance checklist:

1. Open the dashboard source in Obsidian or copy it into a disposable dashboard vault.
2. Confirm the review queue is readable without needing source-code context.
3. Confirm Dataview-facing sections cover:
   - review queue;
   - proposal index;
   - report index;
   - task index.
4. Confirm status labels are limited to:
   - `proposed`;
   - `needs-review`;
   - `applied`;
   - `rejected`.
5. Confirm every review note/checklist asks for:
   - safety boundary;
   - affected paths;
   - evidence;
   - verification result;
   - explicit decision.
6. Do not publish or backfill the dashboard into the live vault without the normal proposal/apply gate.

CLI evidence already available:

```bash
pytest tests/test_phase07_review_dashboard_docs.py
python3 tools/obsidian_review_dashboard.py list --proposal-root out/proposals --json
python3 tools/obsidian_review_dashboard.py explain --proposal out/proposals/example/proposal.json
```

Manual decision field to record after UI review:

```text
dashboard_visual_acceptance: accepted | needs-fixes
reviewer: Dmitry
notes: <short issue list or OK>
```

## P1.4 Diagram readability checklist

Status: technically accepted; visual readability remains human/manual.

Source files:

- `docs/diagrams/architecture.mmd`
- `docs/diagrams/worker-flow.mmd`
- `docs/diagrams/safety-sequence.mmd`

Generated artifacts:

- `out/diagrams/architecture.svg`
- `out/diagrams/worker-flow.svg`
- `out/diagrams/safety-sequence.svg`
- `out/reports/obslayer-architecture-poc-*.pdf`

Manual acceptance checklist:

1. Open the generated PDF and SVG files.
2. Confirm the architecture diagram explains the human layer, worker layer, safety core, outputs/storage, and GitHub baseline.
3. Confirm the worker-flow diagram explains code, verification, final-report, and human acceptance lanes.
4. Confirm the safety sequence makes refusal, approval, backup, apply, verify, and report boundaries clear.
5. Fix confusing labels in `docs/diagrams/*.mmd`, regenerate, and re-run tests before accepting.

Regeneration command:

```bash
python3 tools/obsidian_diagram_pdf_report.py \
  --adapter-record docs/spec-kit/research/sample-adapter-records/diagram-renderer-mermaid-cli.json \
  --project-root . \
  --diagram-out-dir out/diagrams \
  --report-out-dir out/reports
```

CLI evidence already available:

```bash
pytest tests/test_diagram_pdf_adapter.py
```

Manual decision field to record after visual review:

```text
diagram_visual_acceptance: accepted | needs-fixes
accepted_pdf: out/reports/obslayer-architecture-poc-<timestamp>.pdf
notes: <short issue list or OK>
```

## P2.2 RAG/graph sandbox benchmark contract

Status: benchmark metrics implemented for the local wrapper; sandbox-only.

Existing implementation and evidence:

- plan: `docs/spec-kit/09-rag-graph-sandbox-plan.md`
- adapter record: `docs/spec-kit/research/sample-adapter-records/benmaster82-kwipu.json`
- implementation: `src/obslayer/rag_graph_adapter.py`
- CLI: `tools/obsidian_rag_graph_adapter.py`
- tests: `tests/test_rag_graph_adapter.py`
- prior evaluation: `docs/spec-kit/phase04-rag-graph-evaluation-2026-06-28.md`

Minimum benchmark command:

```bash
python3 tools/obsidian_rag_graph_adapter.py \
  --adapter-record docs/spec-kit/research/sample-adapter-records/benmaster82-kwipu.json \
  --sandbox-vault out/sandbox-vaults/rag-benchmark \
  --out-dir out/reports/rag-benchmark \
  --query "Find notes related to Obsidian Operating Layer." \
  --query "Suggest MOC for automation/safety architecture."
```

Acceptance criteria:

- benchmark vault is a copied sandbox or disposable subset;
- no direct write is enabled;
- outputs are JSON and Markdown reports under `out/reports/`;
- findings are evidence-backed and proposal-only (`executed=false`);
- fixed queries, finding count, wall time, max RSS, cost model, and quality notes are recorded;
- normalized findings can feed `obsidian_proposal_worker.py` without live apply.

Verification:

```bash
pytest tests/test_rag_graph_adapter.py
```

## P2.3 MCP read-only adapter expansion contract

Status: read-only expansion metrics implemented for the local wrapper; sandbox-only.

Existing implementation and evidence:

- plan: `docs/spec-kit/08-mcp-sandbox-plan.md`
- adapter record: `docs/spec-kit/research/sample-adapter-records/cyanheads-obsidian-mcp-server.json`
- implementation: `src/obslayer/mcp_adapter.py`
- CLI: `tools/obsidian_mcp_adapter.py`
- tests: `tests/test_mcp_adapter.py`

Minimum expansion command:

```bash
python3 tools/obsidian_mcp_adapter.py \
  --adapter-record docs/spec-kit/research/sample-adapter-records/cyanheads-obsidian-mcp-server.json \
  --sandbox-vault out/sandbox-vaults/mcp-benchmark \
  --out-dir out/reports/mcp-benchmark \
  --probe-tool read_note \
  --probe-tool search_notes \
  --probe-tool write_note
```

Acceptance criteria:

- MCP candidate runs against a sandbox copy, not a writable live vault;
- read/search/graph-like tools return source-path evidence;
- dangerous tools are refused;
- write-like intent becomes proposal-required and `executed=false`;
- JSON and Markdown reports are produced under `out/reports/`;
- probe count, source path count/sample, wall time, max RSS, and cost model are recorded;
- no secret, token, or environment dump is exposed.

Verification:

```bash
pytest tests/test_mcp_adapter.py
```

## Done criteria for this addendum

This addendum is accepted when:

- it is linked from `00-overview.md` and `13-next-improvements-roadmap.md`;
- tests verify the checklist/contract content stays present;
- `make verify` passes;
- GitHub is synchronized;
- any actual human visual/UI acceptance decision is recorded separately after Dmitry reviews Obsidian/PDF/SVG output.
