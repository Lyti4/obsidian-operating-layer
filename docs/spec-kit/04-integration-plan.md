# Integration Plan

## Phase 1 — no-install evaluation

- Keep JSON inventory under `docs/spec-kit/research/`.
- Read README/license for top candidates via GitHub API.
- Pick 2 MCP candidates + 1 RAG/search candidate + 5 Obsidian plugins.
- 2026-06-28 refresh outcome: use `cyanheads/obsidian-mcp-server` as primary MCP sandbox candidate and `benmaster82/Kwipu` as primary Phase 04 RAG/graph candidate; keep `rps321321/obsidian-mcp-pro`, `bettyguo/obsidian_mcp`, `takeshy/obsidian-local-llm-hub`, `swarmclawai/swarmvault`, and `deeflect/dory` as secondary references/pattern sources until separately sandboxed.

## Phase 2 — sandbox

2026-06-28 Phase 04 result: `benmaster82/Kwipu` evaluated through a local sandbox-only RAG/graph wrapper. Promote the normalized finding schema and CLI wrapper; defer full Kwipu install/Ollama indexing until a larger copied-vault benchmark is explicitly scheduled.

- Install/clone only into sandbox after explicit scope decision.
- Run against a copied test vault, not live vault.
- Disable direct write or wrap writes into proposal worker.

## Phase 3 — glue adapters

- Add adapter metadata files.
- Build read/search/propose calls.
- Feed outputs into `tools/obsidian_propose.py` format.
- Add a diagram/PDF rendering adapter for human-facing architecture reports.

## Phase 3.5 — diagrams and PDF reports

- Pick a ready diagram toolchain instead of building rendering from scratch.
- Preferred path: Markdown + Mermaid/Excalidraw-style source in Obsidian, exported to polished PDF.
- CLI path for automation: Mermaid CLI, D2, Graphviz, PlantUML, or Typst/Quarto templates.
- Outputs must be reproducible from source files committed in the project.
- Generated PDFs go under `out/reports/` first; publishing into Obsidian requires the normal proposal/apply safety gate.
- Required use cases:
  - architecture maps;
  - worker orchestration flow;
  - safety/write-gate sequence diagrams;
  - component dependency diagrams;
  - before/after vault curation maps.

## Phase 4 — controlled autonomy

- scheduled observe/index;
- generated reports/proposals;
- auto-apply only safe reports/index notes if approved by policy;
- all vault edits remain approval-gated.
