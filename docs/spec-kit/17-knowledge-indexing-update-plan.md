# 17 — Knowledge Indexing Update Plan

Status: architecture plan; execution state superseded by `20-indexing-runtime-acceptance.md`  
Date: 2026-06-28  
Scope: Obsidian Operating Layer read-only knowledge indexing upgrade

## Decision

Upgrade indexing in phases. Keep Obsidian as the source of truth and treat all indexes as derived,
rebuildable artifacts. The indexer must not mutate the live vault. Any future note changes still go
through the existing Operating Layer safety path:

```text
observe → propose → review → dry-run → approval → backup → apply → verify
```

## Current state

The project already has a shallow read-only layer:

- markdown discovery;
- wikilink extraction;
- tag/frontmatter extraction;
- graph/RAG findings;
- proposal-only outputs for missing links, orphans, backlink candidates, MOC candidates.

Missing layer:

- persistent lexical/semantic catalog for the whole vault;
- source-span provenance for search results;
- rebuildable vector sidecar;
- read-only MCP/search adapter for Hermes.

## Target architecture

```text
Obsidian vault snapshot
  ↓
normalized catalog: files, frontmatter, tags, wikilinks, chunks, hashes
  ↓
SQLite FTS5 + graph tables
  ↓
optional semantic sidecar: local embeddings + vector search
  ↓
read-only MCP/search adapter
  ↓
Hermes reasoning and proposal generation
```

## Non-negotiable requirements

- Vault is the source of truth; index is a cache.
- Full rebuild must be possible from a vault snapshot.
- No write/delete/move tools exposed by the index adapter.
- Protected paths excluded: `.obsidian`, `_Backups`, `.trash`, generated `out/`, archives, binary/system folders.
- Every result must include provenance: absolute or vault-relative path, chunk/span, quote/snippet, content hash/version.
- Cloud/paid embeddings are disabled unless explicitly approved.
- Semantic search is optional; lexical/graph search must still work without it.

## Candidate review decision

Deep static review narrowed the first integration path:

1. **Primary sandbox target: `DalecB/obsidian-semantic-mcp`.**
   - Best safety fit: MCP exposes `search_notes`, `read_note`, `index_vault`, `index_status` only.
   - No vault write/delete/move tools found.
   - Uses local SQLite FTS5 + Ollama embeddings as a derived index.
   - Has chunk/line provenance suitable for Operating Layer acceptance evidence.
   - Blockers before production: Node 24 requirement, remote `OLLAMA_BASE_URL` policy, reindex-on-policy-change rule, project maturity.

2. **Secondary controlled backend: `pvliesdonk/markdown-vault-mcp`.**
   - Stronger maturity and richer FTS5/vector/frontmatter/indexing feature set.
   - Not direct-safe: exposes write/edit/delete/rename/move/fetch/git/upload surfaces.
   - Only evaluate behind `READ_ONLY=true` plus host-side MCP tool filtering.

3. **Graph-RAG experiment: `benmaster82/Kwipu`.**
   - Useful for quality comparison of local Graph RAG over Markdown/Obsidian.
   - Not a base integration target until provenance, protected-path policy, tests/CI, and cloud-model defaults are addressed.

Do not connect any candidate to live apply. The spike only answers whether it can be used as a read-only
search backend behind Operating Layer.

## First spike

Current execution/acceptance state is captured in `20-indexing-runtime-acceptance.md`. The original spike plan below is retained as historical planning context.

Evaluate `DalecB/obsidian-semantic-mcp` on a sandbox vault copy only. If Node 24 blocks the run, record
that as a blocker and either install an isolated Node 24 toolchain for the sandbox or switch the spike to
`pvliesdonk/markdown-vault-mcp` behind read-only/tool-filter guards.

## Acceptance tests

- Rebuilding the index does not change the vault tree or note hashes.
- Protected paths do not appear in catalog, FTS, graph, or vector data.
- Query results include source spans and reproducible provenance.
- Changing/deleting a sandbox note is reflected after rebuild or incremental refresh.
- Semantic sidecar can be disabled without breaking lexical search.
- MCP adapter refuses or does not expose write/delete/move operations.
- Index artifacts are stored under `out/` and can be regenerated from source.
- Same snapshot plus same config produces stable catalog counts and deterministic hashes.

## Sandbox spike steps

1. Create a sandbox vault copy under `out/`.
2. Configure protected-path exclusions before first index build:
   - `.obsidian/`
   - `_Backups/`
   - `.trash/`
   - generated `out/`
   - hidden/system/service directories
3. Force local embeddings only:
   - `OLLAMA_BASE_URL=http://localhost:11434`
   - no OpenAI/cloud provider variables
4. Build the index and capture index metadata, tool list, path policy, and counts.
5. Run a fixed query set covering tags, wikilinks, headings/chunks, and semantic concepts.
6. Verify each result contains path + lines/chunk + snippet + enough hash/version context for audit.
7. Modify/delete only sandbox notes and verify rebuild/incremental update behavior.
8. Rebuild from scratch and compare stable counts/hashes/results.
9. Emit a Markdown + JSON scorecard under `out/`.

## Guardrails

- Index artifacts are derived cache, never source of truth.
- Any remote/cloud embedding endpoint is disabled unless explicitly approved.
- Rebuild the index after changing exclude/sensitive/protected-path policy.
- Any backend with write-like tools must be wrapped so Hermes only sees read/search/status/index tools.
- Live vault mutations remain exclusively inside the existing approval-manifest apply path.

## Implementation notes

Prefer glue around an existing local/FOSS component before writing a custom vector engine. The local
project should own the safety boundary, artifact layout, protected-path filters, and acceptance tests.
The durable architecture remains **FTS5 + graph first, semantic sidecar second**.

## Harness implementation status

Implemented the first no-write sandbox harness:

- library: `src/obslayer/indexing_spike.py`
- CLI: `tools/obsidian_indexing_spike.py`
- candidate record: `docs/spec-kit/research/sample-adapter-records/dalecb-obsidian-semantic-mcp.json`
- tests: `tests/test_indexing_spike.py`
- Make target: `make indexing-spike`

The harness does not execute external candidate code yet. It verifies the declared candidate contract, sandbox-only path, exposed MCP tools, local-only embedding policy, protected-path policy, provenance policy, derived storage declaration, and before/after sandbox vault tree hash.

Independent review findings are now closed:

- report writes are refused unless `--out-dir` resolves under `out/reports/indexing-spike`;
- report writes inside `/home/hermesadmin/Obsidian` are refused even if the path shape matches;
- sandbox vaults must resolve under `out/sandbox-vaults/<name>`, not merely contain the substring `sandbox`;
- candidate records must declare `remote_endpoint_requires_explicit_approval=true` for embedding endpoints;
- tests cover schema validation, bad sandbox root, bad report root, and live-vault report refusal.

First exercised run:

```bash
make indexing-spike
```

The Make target creates/resets the sandbox copy first via `tools/obsidian_sandbox.py`, then runs the no-write scorecard.

Result:

- sandbox copy created under `out/sandbox-vaults/indexing-spike`
- copied files: 663
- copied dirs: 101
- protected/source-sensitive paths skipped by sandbox policy
- `DalecB/obsidian-semantic-mcp` contract evaluation: `passed`
- acceptance booleans all true
- reports:
  - `out/reports/indexing-spike/indexing-spike-evaluation-DalecB-obsidian-semantic-mcp.json`
  - `out/reports/indexing-spike/indexing-spike-evaluation-DalecB-obsidian-semantic-mcp.md`

## Next step

Move from contract/no-write harness to an isolated external-run spike for `DalecB/obsidian-semantic-mcp`: resolve Node 24 in an isolated sandbox toolchain, start only against the sandbox vault, force localhost Ollama, run real `index_vault/search_notes/read_note/index_status`, and compare results against the harness scorecard.

## 2026-07-02 graph-first safety update

To reduce server risk, the semantic roadmap now requires a graph-first pass before any routine embedding work.

Default order:

```text
sandbox snapshot
  ↓
Graphify/Nanobot semantic graph on gpt-5.4-mini
  ↓
reviewed clusters / links / duplicates / cleanup candidates
  ↓
optional embedding candidate set
  ↓
separate bounded embedding slice, if approved
```

The Graphify/Nanobot stage must not start local embeddings automatically and must not mutate the live vault. It produces proposal-only artifacts for Hermes review. The embedding sidecar remains optional and derived; it is not required for lexical/graph acceptance.

See `25-nanobot-graphify-worker.md` for worker routing and stop conditions.


## Graphify-derived embedding handoff

Embedding work must now consume a reviewed Graphify output first. The accepted handoff is:

```text
sandbox snapshot
  ↓
Graphify extract / cluster-only / query-path-explain
  ↓
graphify-out/graph.json + GRAPH_REPORT.md
  ↓
obslayer graphify embedding handoff manifest
  ↓
optional bounded embedding runner consumes only manifest candidates
```

Use `tools/obsidian_graphify_embedding_handoff.py` to create `embedding-manifest.json` and `REPORT.md` from `graphify-out/graph.json`. The handoff selects only eligible sandbox markdown/text source files referenced by Graphify nodes, scores them by graph participation, records hashes, and marks `embedding_policy.auto_execute=false`. It does not start embeddings. A later embedding runner must use that manifest as its allowlist, keep concurrency `1`, checkpoint/resume, write only derived cache under `out/external-indexing-spike/graphify-derived/`, and stop before live vault mutation.
