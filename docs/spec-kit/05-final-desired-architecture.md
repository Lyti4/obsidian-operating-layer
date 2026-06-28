# Final Desired Architecture — Obsidian Operating Layer

Дата: 2026-06-28

## Цель

Собрать production-ready Obsidian operating layer из готовых рабочих компонентов, где наш код остаётся тонким safety/glue слоем.

Система должна:

- читать и индексировать vault;
- строить граф связей, backlinks, orphan notes, candidate MOCs;
- искать по markdown, metadata, BM25/vector/RAG;
- предлагать чистку, объединение, связи, MOC, отчёты;
- рисовать красивые схемы и собирать PDF для Дмитрия;
- никогда не давать внешним компонентам прямую живую запись в vault;
- применять изменения только через obslayer proposal/apply gate.

## Главный принцип сборки

```text
Ready component first → adapter/glue second → our safety gate always last
```

Не строим с нуля то, что уже есть как рабочий plugin/server/library.

## Финальный слойный дизайн

```text
┌─────────────────────────────────────────────────────────────┐
│ Human/UI layer                                               │
│ Obsidian, Dataview, Templater, Tasks, Linter, Omnisearch,    │
│ Metadata Menu, Tag Wrangler, Auto Note Mover, diagrams/PDF   │
└───────────────────────────────┬─────────────────────────────┘
                                │ read/render/report
┌───────────────────────────────▼─────────────────────────────┐
│ Worker/MCP layer                                             │
│ MCP read/search tools, graph workers, RAG workers, report    │
│ workers, diagram renderer, plugin scout                      │
└───────────────────────────────┬─────────────────────────────┘
                                │ proposal bundle only
┌───────────────────────────────▼─────────────────────────────┐
│ Obslayer safety core                                         │
│ observe → propose → verify → apply                           │
│ dry-run default, approval manifest, backup, post-verify      │
└───────────────────────────────┬─────────────────────────────┘
                                │ approved live writes only
┌───────────────────────────────▼─────────────────────────────┐
│ Vaults                                                       │
│ /home/hermesadmin/Obsidian and approved test/sandbox vaults  │
└─────────────────────────────────────────────────────────────┘
```

## Component choices

### 1. Safety core — keep ours

Canonical implementation stays in:

- `tools/obsidian_observe.py`
- `tools/obsidian_propose.py`
- `tools/obsidian_verify.py`
- `tools/obsidian_apply.py`
- shared policy in `src/obslayer/`

Reason: this is the trust boundary. External code can be useful, but live mutation must remain controlled by our exact proposal/manifest/backup/verify contract.

### 2. Obsidian UI/plugins — use community plugins

Initial preferred set:

- Dataview — dashboards and structured queries;
- Templater — report/proposal/MOC templates;
- Linter — markdown/frontmatter normalization;
- Tasks — task layer;
- Omnisearch — local search UI;
- Metadata Menu — metadata editing/quality;
- Tag Wrangler — tag rename/merge workflow;
- Auto Note Mover — rule-based routing, only after sandbox validation;
- Mermaid/Excalidraw-style workflow — diagrams in notes.

Rule: plugins may support UI and local workflows, but automated mutation still goes through obslayer unless Дмитрий explicitly approves a scoped manual plugin operation.

### 3. MCP bridge — use ready servers, disable direct writes

Candidate priority:

1. `cyanheads/obsidian-mcp-server` — primary MCP candidate for broad read/search/frontmatter tooling.
2. `rps321321/obsidian-mcp-pro` — richer graph/canvas/link analysis candidate.
3. `bettyguo/obsidian_mcp` — Python-friendly simpler integration candidate.

Adapter rule:

```json
{
  "direct_write_enabled": false,
  "allowed": ["read", "search", "graph", "metadata-read", "write-request"],
  "forbidden": ["write-direct", "delete-direct", "move-direct"]
}
```

Any write-like MCP output becomes an obslayer proposal, not a filesystem change.

### 4. Retrieval/RAG/graph — use ready engines

Candidate priority:

1. `benmaster82/Kwipu` — local Graph RAG for markdown/Obsidian; good fit for wikilinks/YAML/frontmatter.
2. `takeshy/obsidian-local-llm-hub` — local AI hub with RAG/workflows/edit history; evaluate as Obsidian-side automation shell.
3. `swarmclawai/swarmvault` — local-first knowledge graph/memory pattern source.
4. `deeflect/dory` — markdown memory layer with CLI/HTTP/MCP patterns.

Expected outputs:

- related notes;
- missing backlinks;
- orphan notes;
- duplicate/merge candidates;
- stale/cold notes;
- candidate MOCs;
- queryable memory/context index.

### 5. Worker orchestration — small local queue first

Start with a simple local durable queue, not a heavy distributed system.

Recommended shape:

```json
{
  "task_id": "obslayer-YYYYMMDD-HHMMSS-kind",
  "worker": "linker-worker",
  "vault_root": "/home/hermesadmin/Obsidian",
  "capabilities": ["read", "search", "graph", "propose"],
  "inputs": {},
  "outputs": {
    "report": "out/reports/...md",
    "proposal": "out/proposals/...json"
  },
  "write_policy": "proposal_only"
}
```

Initial workers:

- `plugin-scout` — keeps registry/GitHub candidate inventory fresh through `gh api` when auth exists;
- `index-worker` — builds markdown/frontmatter/link index;
- `graph-worker` — backlinks, orphans, nonexistent links, clusters, MOCs;
- `retrieval-worker` — BM25/vector/RAG search;
- `linker-worker` — candidate links/backlinks;
- `dedupe-worker` — possible duplicates and merge candidates;
- `cleaner-worker` — formatting, stale metadata, empty notes, unsafe paths excluded;
- `memory-consolidator` — proposes summaries and memory maps, no direct Soul edits;
- `diagram-worker` — generates architecture diagrams and PDF reports;
- `proposal-worker` — normalizes all suggested changes into obslayer proposal format;
- `report-worker` — writes human reports under safe output paths.

### 6. Diagram/PDF layer — required deliverable layer

Purpose: Hermes must be able to show Dmitry clear visual architecture and process diagrams as polished PDFs.

Ready tooling candidates:

- Obsidian Mermaid blocks for diagrams inside notes;
- Excalidraw-style Obsidian workflow for nicer human-facing sketches;
- Mermaid CLI for automated SVG/PDF export;
- D2 for clean architecture diagrams from text;
- Graphviz for dependency/graph outputs;
- PlantUML for sequence/component diagrams;
- Typst or Quarto for final PDF assembly from Markdown + diagrams.

Policy:

- source diagrams are committed as text where possible;
- generated PDFs go to `out/reports/` first;
- publishing PDFs/notes into Obsidian uses proposal/apply if automated;
- diagrams must cover worker flow, safety gate, component map, and before/after vault curation.

### 7. LLM policy

Default path must work without LLM.

Allowed optional LLM uses:

- summarization;
- title/MOC suggestions;
- candidate link explanation;
- classification;
- report wording;
- diagram labels.

Forbidden LLM uses:

- final decision to delete/move/merge live notes;
- bypassing approval manifest;
- reading or emitting secrets;
- direct filesystem mutation.

Preferred local/low-cost options:

- local Qwen/Ollama/LM Studio/vLLM-style OpenAI-compatible endpoint;
- Nous/free hosted model only for non-secret summaries if explicitly approved and safe.

## Mutation flow

```text
observe/index
  ↓
workers produce findings
  ↓
proposal-worker creates proposal bundle
  ↓
verify proposal target/risk/safety
  ↓
Dmitry approval manifest
  ↓
apply creates backup and writes narrowly scoped changes
  ↓
post-verify compares expected vs actual
  ↓
report-worker writes acceptance report
```

## Capability matrix

| Capability | External plugins/MCP/RAG | Obslayer safety core | Notes |
|---|---:|---:|---|
| read markdown | yes | yes | allowed |
| search/index | yes | yes | allowed |
| graph analysis | yes | yes | allowed |
| render diagrams/PDF | yes | yes | output first under `out/reports/` |
| create proposal | yes | yes | proposal only |
| direct write | no | only with manifest | external direct writes disabled |
| delete/move/merge | no | only with explicit approval | highest risk |
| touch protected paths | no | no | refused |
| secrets handling | no | no | never print/store secrets |

## Protected areas

Protected by default:

- `.obsidian`
- `_Backups`
- `_Archive`
- `.trash`
- Soul-protected areas
- secrets, tokens, browser profiles, private keys, `.env`

## Sandbox-first evaluation plan

1. Keep research artifacts under `out/research/`.
2. Clone/install selected components only after scope decision.
3. Run components against copied test vault.
4. Disable direct write features or wrap them with proposal-only adapter.
5. Capture commands, outputs, risks, license, and compatibility notes.
6. Promote only components that can operate under this safety contract.

## Final acceptance criteria

A component or worker is accepted only when:

- it has a documented adapter contract;
- direct writes are disabled or impossible;
- output can be converted to proposal/report format;
- sandbox run succeeds on copied vault;
- verification command is recorded;
- risks and license are recorded;
- live vault mutation remains behind obslayer apply.

## Next implementation package

Build next in this order:

1. `adapters/` metadata schema for external components.
2. Local queue/task JSON schema.
3. Read-only MCP adapter sandbox.
4. Graph/RAG adapter sandbox.
5. Diagram/PDF rendering proof-of-concept.
6. Proposal normalization from worker outputs.
7. Human review dashboard in Obsidian using Dataview/Templater.
