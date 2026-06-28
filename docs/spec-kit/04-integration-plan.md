# Integration Plan

## Phase 1 — no-install evaluation

- Keep JSON inventory under `out/research/`.
- Read README/license for top candidates via GitHub API.
- Pick 2 MCP candidates + 1 RAG/search candidate + 5 Obsidian plugins.

## Phase 2 — sandbox

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
