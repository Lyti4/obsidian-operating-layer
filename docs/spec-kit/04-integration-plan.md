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

## Phase 4 — controlled autonomy

- scheduled observe/index;
- generated reports/proposals;
- auto-apply only safe reports/index notes if approved by policy;
- all vault edits remain approval-gated.
