# Manual and Adapter Acceptance Addendum

## Purpose

This addendum closes the remaining non-code acceptance evidence for `13-next-improvements-roadmap.md` and defines the sandbox-only contracts for the next adapter capability work.

It does not approve live vault mutation. All live-vault usage remains read-only, proposal-only, or dry-run unless a separate approval manifest explicitly authorizes a narrow apply.

## P1.3 Dashboard field review checklist

Status: accepted by Hermes server-side manual review. Live Obsidian publication is still gated.

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

Recorded manual decision:

```text
dashboard_visual_acceptance: accepted
reviewer: Hermes Agent on server, because Dmitry cannot open server files directly
notes: Dashboard source is readable, Dataview sections cover review/proposal/report/task indexes, status labels are constrained, and review template records safety boundary, evidence, verification result, and explicit decision.
```

## P1.4 Diagram readability checklist

Status: accepted by Hermes server-side manual review using real Mermaid-rendered SVG artifacts.

Source files:

- `docs/diagrams/architecture.mmd`
- `docs/diagrams/worker-flow.mmd`
- `docs/diagrams/safety-sequence.mmd`

Generated artifacts reviewed:

- `out/diagrams/manual-acceptance/architecture.svg`
- `out/diagrams/manual-acceptance/worker-flow.svg`
- `out/diagrams/manual-acceptance/safety-sequence.svg`
- `out/reports/manual-acceptance/obslayer-architecture-poc-20260628-102653Z.pdf`

Renderer evidence:

```text
renderer: npx @mermaid-js/mermaid-cli 11.15.0
browser mode: bundled Chromium with --no-sandbox in temporary puppeteer config
architecture.svg: rendered flowchart, 47770 bytes, not source-preview fallback
worker-flow.svg: rendered flowchart, 119073 bytes, not source-preview fallback
safety-sequence.svg: rendered sequence diagram, 34097 bytes, not source-preview fallback
pdf header: %PDF-
```

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

Recorded manual decision:

```text
diagram_visual_acceptance: accepted
reviewer: Hermes Agent on server, because Dmitry cannot open server files directly
accepted_pdf: out/reports/manual-acceptance/obslayer-architecture-poc-20260628-102653Z.pdf
notes: Architecture, worker-flow, and safety-sequence diagrams render as actual Mermaid SVG diagrams. Labels identify human decision layer, ready Obsidian components, worker layer, safety core, storage/outputs, code/verification/final-report lanes, and refusal/approval/backup/apply/verify/report boundaries.
```

## P2.2 RAG/graph sandbox benchmark contract

Status: benchmark metrics implemented and exercised on a copied sandbox vault; sandbox-only.

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

Latest sandbox evidence:

```text
out/reports/rag-benchmark-20260628-095744Z/rag-graph-evaluation-benmaster82-Kwipu-20260628-095759Z.json
out/reports/rag-benchmark-20260628-095744Z/rag-graph-evaluation-benmaster82-Kwipu-20260628-095759Z.md
```

Recorded evidence fields:

```text
sandboxed: true
direct_write_disabled: true
normalized_findings_only: true
proposal_only_for_write_like_suggestions: true
notes_scanned: 627
fixed_query_count: 2
finding_count: 7869
benchmark_metrics.cost_model: local-wrapper-no-llm-call
benchmark_metrics.wall_time_ms: 13885.955
benchmark_metrics.max_rss_kb: 35272
```

## P2.3 MCP read-only adapter expansion contract

Status: read-only expansion metrics implemented and exercised on a copied sandbox vault; sandbox-only.

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

Latest sandbox evidence:

```text
out/reports/mcp-benchmark-20260628-095744Z/mcp-adapter-evaluation-cyanheads-obsidian-mcp-server-20260628-095759Z.json
out/reports/mcp-benchmark-20260628-095744Z/mcp-adapter-evaluation-cyanheads-obsidian-mcp-server-20260628-095759Z.md
```

Recorded evidence fields:

```text
sandboxed: true
direct_write_disabled: true
dangerous_tools_refused: true
probe_count: 5
source_path_count: 627
benchmark_metrics.cost_model: local-wrapper-no-llm-call
benchmark_metrics.wall_time_ms: 16.946
benchmark_metrics.max_rss_kb: 20220
```

## Done criteria for this addendum

This addendum is accepted when:

- it is linked from `00-overview.md` and `13-next-improvements-roadmap.md`;
- tests verify the checklist/contract content stays present;
- `make verify` passes;
- GitHub is synchronized;
- manual visual/UI acceptance is recorded in this addendum by Hermes Agent when Dmitry cannot open server-local files directly.
