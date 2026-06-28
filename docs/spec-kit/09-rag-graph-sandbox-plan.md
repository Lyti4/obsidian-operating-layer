# RAG and Graph Sandbox Plan

## Goal

Use ready local RAG/graph engines to produce high-quality note relationships, memory maps, MOC candidates, duplicate candidates, and cleanup proposals.

## Candidate order

1. `benmaster82/Kwipu` — Markdown/Obsidian Graph RAG, wikilinks/YAML/frontmatter focus.
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
