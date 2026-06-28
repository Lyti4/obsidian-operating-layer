# RAG and Graph Sandbox Plan

## Goal

Use ready local RAG/graph engines to produce high-quality note relationships, memory maps, MOC candidates, duplicate candidates, and cleanup proposals.

## Candidate order

2026-06-28 GitHub refresh source: `docs/spec-kit/research/github-components-refresh-2026-06-28.md`.

1. `benmaster82/Kwipu` — Markdown/Obsidian Graph RAG, wikilinks/YAML/frontmatter focus; primary Phase 04 sandbox candidate.
2. `takeshy/obsidian-local-llm-hub` — Obsidian-side local AI hub/RAG/workflows/edit history.
3. `swarmclawai/swarmvault` — local-first knowledge graph/memory design patterns.
4. `deeflect/dory` — markdown memory layer with CLI/HTTP/MCP patterns.

## Expected outputs

- related notes with evidence;
- candidate backlinks;
- orphan notes;
- nonexistent links;
- duplicate or merge candidates;
- cluster/MOC candidates;
- stale metadata and classification suggestions;
- memory consolidation maps.

## Sandbox data policy

Use copied vault or narrow read-only safe subset first. Exclude:

- `.obsidian`
- `_Backups`
- `_Archive`
- `.trash`
- Soul-protected areas unless explicitly scoped
- secrets, `.env`, credentials, browser profiles

## Evaluation workflow

```text
prepare sandbox subset
  ↓
run index/build command
  ↓
run fixed test queries
  ↓
export findings
  ↓
normalize to obslayer finding schema
  ↓
turn write-like suggestions into proposal only
```

## Fixed test queries

- Find notes related to Obsidian Operating Layer.
- Find orphan notes with high connection potential.
- Suggest MOC for automation/safety architecture.
- Detect possible duplicates among project reports.
- Suggest backlinks for final architecture spec.

## Acceptance criteria

- Runs locally or with explicitly approved endpoint.
- Does not require cloud secrets by default.
- Produces evidence-backed outputs.
- Can export machine-readable findings or parseable markdown.
- Does not mutate vault directly.
- Runtime/resource cost is acceptable.

## Phase 04 sandbox result

2026-06-28 result: `benmaster82/Kwipu` remains the primary ready RAG/graph candidate, evaluated through the local wrapper `tools/obsidian_rag_graph_adapter.py` against a copied sandbox vault only.

- adapter record: `docs/spec-kit/research/sample-adapter-records/benmaster82-kwipu.json`
- implementation: `src/obslayer/rag_graph_adapter.py`
- tests: `tests/test_rag_graph_adapter.py`
- human report: `docs/spec-kit/phase04-rag-graph-evaluation-2026-06-28.md`

The current slice normalizes findings only: nonexistent links, orphan notes, candidate backlinks, MOC clusters, duplicate candidates, and graph summaries. All write-like outcomes are proposal-only and record `executed=false`; no live vault path is used.
