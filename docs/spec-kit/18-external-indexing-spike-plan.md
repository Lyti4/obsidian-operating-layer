# 18 — External Indexing Spike Plan

Status: ready for sandbox-only execution  
Date: 2026-06-28  
Scope: real external-run spike for `DalecB/obsidian-semantic-mcp` against a sandbox vault copy only

## Goal

Move from the contract/no-write scorecard to a real execution proof for `DalecB/obsidian-semantic-mcp` without connecting it to the live vault.

The spike must answer:

- Can the MCP server run under an isolated Node 24 toolchain on this host?
- Does `index_vault` mutate only derived index storage and not the sandbox notes?
- Do `search_notes` and `read_note` return usable path/heading/line/snippet provenance?
- Does keyword-only mode still work if local Ollama embeddings are unavailable?
- Does the runtime refuse/avoid protected paths and symlink escapes?

## Current prerequisites discovered

- Host Node: `v22.22.3`; candidate requires Node `>=24.0.0`.
- `corepack`: available.
- Docker: available, but container access to host-local Ollama needs care.
- Ollama on `http://localhost:11434`: not running at this check, so semantic mode is blocked until Ollama + `bge-m3` are available.
- No host-wide Node upgrade should be done for the spike.

## Isolation strategy

Use a throwaway tool/runtime home under `out/`, never the live vault:

```text
out/sandbox-vaults/indexing-spike/          # sandbox vault copy
out/external-indexing-spike/node-home/      # npm/cache/home for the external candidate
out/external-indexing-spike/mcp-home/       # OBSIDIAN_SEMANTIC_MCP_HOME derived index
out/reports/external-indexing-spike/        # JSON/MD evidence
```

Preferred Node 24 path:

```bash
npx -y -p node@24 node --version
```

If that works, run the candidate with the same isolated npm invocation rather than changing system Node.

Fallback path:

- use Docker `node:24-bookworm` only if the npm Node shim fails;
- mount only sandbox/report/runtime directories;
- do not mount `/home/hermesadmin/Obsidian`;
- do not use Docker for semantic mode unless localhost-only Ollama access can be preserved without redirecting to a remote endpoint.

## Environment contract

Required environment for all candidate invocations:

```bash
export OBSIDIAN_VAULT_ROOT="$PWD/out/sandbox-vaults/indexing-spike"
export OBSIDIAN_SEMANTIC_MCP_HOME="$PWD/out/external-indexing-spike/mcp-home"
export OBSIDIAN_SEMANTIC_STARTUP_INDEX=false
export OBSIDIAN_EMBED_MODEL=bge-m3
export OLLAMA_BASE_URL=http://localhost:11434
export HOME="$PWD/out/external-indexing-spike/node-home"
export npm_config_cache="$PWD/out/external-indexing-spike/npm-cache"
```

Forbidden:

- `OBSIDIAN_VAULT_ROOT=/home/hermesadmin/Obsidian` or any live vault path;
- remote `OLLAMA_BASE_URL`;
- writes outside `out/external-indexing-spike` and `out/reports/external-indexing-spike` except npm cache under the same runtime root;
- enabling candidate startup indexing against live paths.

## Execution phases

### Phase 0 — Prepare sandbox and baseline hashes

```bash
make indexing-sandbox
python3 tools/obsidian_indexing_spike.py \
  --candidate-record docs/spec-kit/research/sample-adapter-records/dalecb-obsidian-semantic-mcp.json \
  --sandbox-vault out/sandbox-vaults/indexing-spike \
  --out-dir out/reports/indexing-spike
```

Capture:

- sandbox path;
- file count/dir count;
- before tree hash;
- scorecard status.

### Phase 1 — Node 24 smoke without candidate install

```bash
mkdir -p out/external-indexing-spike/node-home out/external-indexing-spike/npm-cache
HOME="$PWD/out/external-indexing-spike/node-home" \
npm_config_cache="$PWD/out/external-indexing-spike/npm-cache" \
npx -y -p node@24 node --version
```

Acceptance: prints `v24.x` and writes only inside `out/external-indexing-spike`.

### Phase 2 — Candidate setup/introspection

Run setup/help first; do not index yet:

```bash
HOME="$PWD/out/external-indexing-spike/node-home" \
npm_config_cache="$PWD/out/external-indexing-spike/npm-cache" \
npx -y -p node@24 -p @dalecb/obsidian-semantic-mcp \
  obsidian-semantic-mcp-setup
```

Capture package version, available command, and any config instructions into the report.

### Phase 3 — Real MCP tool calls

Use a small stdio MCP probe script, not Codex MCP config, so the test remains hermetic. The probe should:

1. spawn the MCP server with the environment contract above;
2. initialize MCP over stdio;
3. list tools;
4. call `index_status`;
5. call `index_vault` with `{ "mode": "full" }` or the documented equivalent;
6. call `search_notes` for the fixed queries;
7. call `read_note` on one returned path/line range;
8. call `index_status` again;
9. write raw sanitized JSON transcript to `out/reports/external-indexing-spike/`.

Fixed queries:

- `Obsidian Operating Layer safety boundary`
- `approval manifest backup apply verify`
- `wikilinks tags frontmatter knowledge graph`

### Phase 4 — Safety checks

After the run:

- compare sandbox tree hash before/after, excluding only candidate derived index root if it is inside the sandbox — preferred config keeps it outside sandbox;
- assert no files appeared under `/home/hermesadmin/Obsidian`;
- assert derived SQLite/artifacts live only under `out/external-indexing-spike/mcp-home`;
- assert exposed tools are only `index_status`, `index_vault`, `search_notes`, `read_note`;
- assert all search/read evidence includes path + line/chunk/snippet provenance;
- assert protected paths do not appear in results or index metadata.

### Phase 5 — Semantic/keyword split

If Ollama is not running:

- record semantic mode as blocked by `localhost:11434 unavailable`;
- still attempt keyword mode if supported by `search_notes { "mode": "keyword" }`;
- do not substitute cloud/remote embeddings.

If Ollama is running:

- verify `bge-m3` exists;
- if missing, ask before pulling if model download size/cost/time is material;
- run hybrid and semantic searches;
- compare with keyword results.

## Acceptance gates

Pass only if all true:

- Node 24 runs in isolated user/cache path; host Node remains unchanged.
- Candidate sees only `out/sandbox-vaults/indexing-spike` as vault root.
- Candidate exposes no write/delete/move/patch/rename tools.
- No live vault mutation occurs.
- Sandbox note tree hash is unchanged by index/search/read.
- Derived artifacts are under `out/external-indexing-spike/mcp-home` and rebuildable.
- Results include source provenance sufficient for Operating Layer audit.
- Remote embeddings are not used.

## Expected report artifacts

```text
out/reports/external-indexing-spike/external-indexing-spike-summary.md
out/reports/external-indexing-spike/external-indexing-spike-transcript.json
out/reports/external-indexing-spike/external-indexing-spike-safety.json
```

## Blockers to resolve before production integration

- Add/keep host-side MCP tool filter even if candidate is read-only today.
- Add a wrapper-level provenance normalizer that injects `hash_or_version`.
- Add a reindex-required marker when protected-path or embedding policy changes.
- Keep live writes exclusively in proposal/approval/apply flow.
