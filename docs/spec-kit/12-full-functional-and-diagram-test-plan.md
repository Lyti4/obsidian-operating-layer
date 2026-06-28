# Full Functional and Diagram Test Plan

## Goal

Use the spec kit as the operating plan for moving the Obsidian Operating Layer from completed MVP phases into field use. The test scope covers the full safety pipeline, controlled-autonomy queue, review/dashboard docs, and diagram/PDF generation.

## Source spec-kit basis

- `00-overview.md` — ready components first; external components may read/search/analyze/render/propose, but direct vault writes are forbidden.
- `03-safety-contract.md` — live mutation path is only `tools/obsidian_apply.py` with approval manifest, backup, and verify.
- `10-diagram-pdf-pipeline.md` — diagrams/PDF are reproducible from text/Obsidian-native sources and generated into `out/` first.
- `11-implementation-roadmap.md` — Phases 5-8 are the current acceptance surface: diagram/PDF, proposal normalization, review dashboard, controlled autonomy.

## Test principles

1. Observe first, propose second, apply only with explicit approval.
2. Live vault access in tests is read-only or dry-run only.
3. Generated artifacts stay under ignored `out/` or temporary `/tmp/hermes-verify-*` paths.
4. Diagram/PDF outputs must be regenerated from committed source files.
5. A pass is not only "tests green": every user-facing flow must produce an inspectable artifact.

## Functional test matrix

| Area | Command / method | Acceptance criteria | Evidence target |
|---|---|---|---|
| Unit/regression suite | `make verify` | pytest, ruff, compileall pass | terminal output |
| Read-only observe | `make smoke` step: `tools/obsidian_observe.py --vault /home/hermesadmin/Obsidian` | returns `status=ok`; no writes | `out/smoke-*/observe.json` |
| Proposal skeleton | `make smoke` step: `tools/obsidian_propose.py` | dry-run proposal with approval phrase, backup plan, no live write | `out/smoke-*/proposal/proposal.json` |
| Proposal verify | `make smoke` step: `tools/obsidian_verify.py` | `ok=true`, `issues=[]` | smoke output |
| Apply dry-run | `make smoke` step: `tools/obsidian_apply.py` without `--apply` | `status=dry-run`, no applied targets | `out/smoke-*/apply-dry-run.json` |
| Proposal worker | pytest + focused CLI when findings are supplied | evidence/risk/targets preserved; protected targets refused | `tests/test_proposal_normalization.py` |
| Sandbox harness | pytest | sandbox copy excludes protected paths and does not mutate live vault | `tests/test_sandbox_harness.py` |
| MCP/RAG adapters | pytest | read/search/analyze/propose only; no direct writes | adapter tests and sample records |
| Review dashboard | pytest + manual Obsidian check | dashboard source notes render and contain status labels/templates | `docs/obsidian-review-dashboard/` |
| Controlled autonomy | temp queue CLI smoke under `/tmp/hermes-verify-*` | create/list/run/report pass; scheduler disabled; applied vs proposed distinguished | temporary acceptance report |
| Backfill report | CLI against safe proposal bundle | Markdown report can be written to chosen reports dir only when intentionally requested | explicit operator run |

## Diagram/PDF test matrix

| Area | Command / method | Acceptance criteria | Evidence target |
|---|---|---|---|
| Diagram source presence | check `docs/diagrams/*.mmd` | architecture, worker-flow, safety-sequence sources exist | committed source files |
| Renderer adapter policy | pytest + adapter record load | direct write disabled; render-only contract enforced | `tests/test_diagram_pdf_adapter.py` |
| SVG generation | `python3 tools/obsidian_diagram_pdf_report.py --adapter-record docs/spec-kit/research/sample-adapter-records/diagram-renderer-mermaid-cli.json --project-root /home/hermesadmin/work/obsidian-operating-layer` | three SVG files generated under `out/diagrams/` | `out/diagrams/*.svg` |
| PDF generation | same command | PDF generated under `out/reports/` and starts with `%PDF-` | `out/reports/obslayer-architecture-poc-*.pdf` |
| Report metadata | same command | JSON/Markdown report includes source paths, generation command, no live vault write | `out/reports/obslayer-architecture-poc-*.json/.md` |
| Visual usefulness | manual review | diagrams are readable and useful, not merely syntactically valid | human acceptance note |

## Fresh verification snapshot — 2026-06-28

Commands executed from `/home/hermesadmin/work/obsidian-operating-layer`:

```bash
make verify && make smoke
python3 tools/obsidian_diagram_pdf_report.py \
  --adapter-record docs/spec-kit/research/sample-adapter-records/diagram-renderer-mermaid-cli.json \
  --project-root /home/hermesadmin/work/obsidian-operating-layer
```

Observed results:

- `make verify`: pytest `54 passed`, ruff `All checks passed!`, compileall passed.
- `make smoke`: observe/propose/verify/apply dry-run completed with `status=ok`; live apply was not performed.
- Diagram/PDF generation: `status=ok`, `direct_write_disabled=true`, `no_live_vault_write=true`, `pdf_generated=true`.
- Generated SVG outputs:
  - `out/diagrams/architecture.svg`
  - `out/diagrams/safety-sequence.svg`
  - `out/diagrams/worker-flow.svg`
- Generated report outputs:
  - `out/reports/obslayer-architecture-poc-20260628-090723Z.json`
  - `out/reports/obslayer-architecture-poc-20260628-090723Z.md`
  - `out/reports/obslayer-architecture-poc-20260628-090723Z.pdf`
- File signature check: SVG files start with `<svg`; PDF starts with `%PDF-`.
- Controlled-autonomy temp queue smoke: create/list/run/report passed under `/tmp/hermes-verify-*`; temp directory was cleaned up.

## Remaining manual checks

1. Open generated PDF and SVGs visually and confirm they are readable enough for Dmitry.
2. Open `docs/obsidian-review-dashboard/index.md` in Obsidian and confirm Dataview/Templater-facing content is usable.
3. Run one real field scenario on a small vault subset: observe → finding/proposal → review → reject/approve decision; do not live-apply without explicit approval.
4. If report backfill into Obsidian is desired, run it as an explicit write task with approval/scope, not as part of automatic testing.

## Next kanban batch proposal

Create a new spec-kit field-test batch rather than more blind implementation:

1. `field_test_slice`: run a real observe/proposal scenario on a small approved vault subset.
2. `diagram_visual_review`: inspect generated diagrams/PDF and collect readability fixes.
3. `dashboard_manual_review`: validate dashboard notes inside Obsidian.
4. `safety_apply_rehearsal`: rehearse approval-manifest apply on a disposable sandbox vault only.
5. `acceptance_report`: summarize findings, gaps, and next P0/P1 fixes.

## Stop conditions

Stop and ask Dmitry before any live vault mutation, destructive operation, production restart, network exposure, paid/high-volume API use, or Soul-governance change.
