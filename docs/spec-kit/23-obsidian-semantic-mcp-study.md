# 23 — Obsidian Semantic MCP Study

Date: 2026-06-29
Project: Obsidian Operating Layer
Package studied: `@dalecb/obsidian-semantic-mcp@0.2.1`
Sources:
- npm metadata: `npm view @dalecb/obsidian-semantic-mcp@0.2.1 --json`
- npm tarball unpacked under `/home/hermesadmin/work/obsidian-operating-layer/out/tmp/obsidian-semantic-mcp-study/package`
- upstream README/troubleshooting from GitHub/npm

## Summary

`@dalecb/obsidian-semantic-mcp` is a young read-only MCP server for semantic retrieval over an Obsidian vault. It reads Markdown files, chunks them, embeds chunks through local Ollama `/api/embed`, and stores a derived SQLite index with FTS5 rows and JSON vectors. It exposes only four tools: `index_status`, `index_vault`, `search_notes`, and `read_note`.

It is aligned with our safety model as a guarded sandbox backend, but not robust enough to expose directly to the live vault without our wrapper. Main reason: indexing is a single long MCP call with no built-in checkpoint/resume/progress report, and upstream has effectively no package tests in the published tarball.

## Version/runtime facts

- Current npm latest: `0.2.1`.
- Published: 2026-06-03.
- License: MIT.
- Repository: `https://github.com/DalecB/obsidian-semantic-mcp`.
- Node engine: `>=24.0.0`.
- Package bins:
  - `obsidian-semantic-mcp`
  - `obsidian-semantic-mcp-setup`
- Published package dependencies: none.
- Verification run against unpacked tarball:
  - command: `npm test`
  - result: pass, but `node --test` discovered `0` tests.

## Environment/config

From `src/config.mjs`:

- `OBSIDIAN_VAULT_ROOT` — required vault root.
- `OBSIDIAN_SEMANTIC_MCP_HOME` — app root, default `~/.obsidian-semantic-mcp`.
- `OBSIDIAN_SEMANTIC_DB` — optional explicit SQLite DB path.
- `OLLAMA_BASE_URL` — default `http://localhost:11434`.
- `OBSIDIAN_EMBED_MODEL` — default `bge-m3`.
- `OBSIDIAN_SEMANTIC_STARTUP_INDEX` — default false; if true, starts background incremental indexing at startup.
- `OBSIDIAN_SEMANTIC_ALLOW_SENSITIVE` — must be true for `include_sensitive` calls.
- `OBSIDIAN_SEMANTIC_TIMEOUT_MS` — per Ollama embed HTTP request timeout, default `60000` ms.
- `OBSIDIAN_SEMANTIC_EXCLUDE` — comma/newline separated always-denied prefixes.
- `OBSIDIAN_SEMANTIC_SENSITIVE_PATHS` — override sensitive prefixes; default `08_PersonalInfo/`.

Important: `OBSIDIAN_SEMANTIC_TIMEOUT_MS` is not an overall indexing timeout. It only bounds individual Ollama embedding HTTP requests.

## Exposed MCP tools

### `index_status`

Returns:
- `vault_root`
- `db_path`
- `embedding_model`
- `last_indexed_at`
- counts: `notes`, `chunks`, `archived`, `sensitive`
- `read_only: true`
- active safety config: startup index, sensitive flag, system denied, excludes, sensitive paths

### `index_vault`

Schema:

```json
{
  "mode": "incremental|full",
  "dry_run": false,
  "paths": ["vault/relative/file.md"],
  "include_sensitive": false
}
```

Behavior from `src/indexer.mjs`:
- If `paths` is absent: scans the whole vault and removes notes from DB that are no longer present in the scan.
- If `paths` is present: indexes only those paths and does not delete unrelated existing DB rows.
- `paths` must be vault-relative Markdown paths; absolute/traversal/non-md paths are rejected.
- In incremental mode, unchanged files are skipped by content hash.
- In full mode, matching files are reindexed even if hash is unchanged.
- Per-file errors are caught, increment `failed`, and are printed to stderr as:
  - `[obsidian-semantic-mcp] index failed for <path>: <message>`
- But errors thrown while resolving requested `paths` happen before the per-file loop and fail the whole MCP call.

Counts returned:
- `indexed`
- `updated`
- `skipped`
- `deleted`
- `failed`
- `dryRun`

### `search_notes`

Schema:

```json
{
  "query": "text",
  "limit": 8,
  "mode": "hybrid|semantic|keyword",
  "folder_include": "prefix/",
  "folder_exclude": "prefix/",
  "include_archived": false,
  "include_sensitive": false
}
```

Behavior:
- `limit` is clamped to 1..30.
- `keyword` mode does not embed the query.
- `semantic`/`hybrid` embed the query via Ollama.
- Vector scoring currently scans all chunk vectors from SQLite into JS and computes cosine in process, then keeps top 120 chunk ids.
- Keyword scoring uses SQLite FTS5 `MATCH` over up to 12 query terms joined by OR.
- Results are grouped by file and return top matched sections/snippets.

### `read_note`

Schema:

```json
{
  "path": "vault/relative/file.md",
  "start_line": 10,
  "end_line": 40,
  "include_sensitive": false
}
```

Behavior:
- Reads directly from filesystem after path guard.
- Always enforces current live config/excludes, independent of stale DB state.

## Indexing internals

From `src/markdown.mjs` and `src/indexer.mjs`:

- Markdown parsing is lightweight custom parsing, not Obsidian-aware parsing.
- For each file, it creates:
  - one summary chunk;
  - section chunks split by Markdown headings;
  - long sections split at about 1200 chars with 160-char overlap.
- Embeddings are requested in batches of 16 chunks per Ollama `/api/embed` call.
- Ollama client concurrency defaults to 1, so embeddings are serialized.
- The in-memory embedding cache is small (`cacheSize=256`) and only process-local.
- Each note replacement is transactional:
  - delete old note/chunks/FTS rows;
  - insert note row;
  - insert chunks and FTS rows;
  - commit.

## SQLite schema

From `src/database.mjs`:

- `meta(key,value)`
- `notes(path,title,mtime_ms,size,hash,tags_json,headings_json,archived,sensitive)`
- `chunks(id,path,kind,title,heading,start_line,end_line,text,raw_text,embedding_json,updated_at)`
- `chunks_fts` FTS5 virtual table with `id,path,title,heading,tags,text`
- `PRAGMA journal_mode = WAL`

Vectors are stored as JSON text, not a vector extension. This is simple and portable, but search scales by scanning vectors in JS.

## Safety model

Built-in always-denied rules:
- any hidden path segment beginning with `.`;
- `.obsidian/`, `.smart-env/`, `.claude/`, `.codex-skill-staging/`, `.codex-semantic-mcp/`;
- any `node_modules`, `cache`, `logs` segment.

User excludes:
- `OBSIDIAN_SEMANTIC_EXCLUDE` prefixes are always denied.

Sensitive paths:
- default `08_PersonalInfo/`;
- blocked unless server env has `OBSIDIAN_SEMANTIC_ALLOW_SENSITIVE=true` and tool call passes `include_sensitive=true`.

Symlink/path safety:
- relative paths are normalized;
- absolute paths and traversal are rejected;
- filesystem realpath must remain inside vault root.

Important mismatch for our vault:
- `_Archive` is not a built-in denied prefix, but our wrapper/exclude config may deny it.
- If a denied path is passed explicitly through `paths`, the whole `index_vault` call fails before per-file loop. Therefore our batched runner must pre-filter protected/excluded paths and record skipped paths itself.

## Reliability and scale observations

1. No native progress reporting.
   - A long `index_vault` call returns only after all candidate paths are processed.
   - During the call, useful details are only on stderr.

2. No native checkpoint/resume.
   - Incremental hashing makes repeated calls safe-ish.
   - But upstream does not store batch progress or expose active file.

3. Requested `paths` support is real and suitable for our batching.
   - Explicit `paths` do not delete DB rows outside that subset.
   - Incremental mode skips unchanged files.
   - This allows our wrapper to implement resumable batches over one derived DB.

4. Explicit `paths` denial is all-or-nothing for that call.
   - Denied path errors happen during `paths.map(resolveRequestedPath)` before entering per-file catch.
   - A single protected path can fail a whole batch.

5. Per-file failures are lossy in the structured MCP response.
   - Response only includes counts.
   - File/error detail is stderr only.
   - Our harness must capture and parse stderr tails/lines if we want a useful buglog.

6. Large vaults will be slow by design.
   - Embedding calls are serialized.
   - Each file can produce many chunks.
   - Search semantic mode scans JSON vectors in JS, not a vector index.

7. Node 24 is a hard runtime requirement.
   - Package uses `node:sqlite` (`DatabaseSync`), which explains Node >=24.
   - Our wrapper must prove the actual server process runs under Node 24, not just that `npx` emitted a warning.

## Direct implications for our implementation

### Keep

- Keep this candidate as sandbox/read-only backend candidate.
- Keep `OBSIDIAN_SEMANTIC_STARTUP_INDEX=false`.
- Keep derived DB under repo-local `out/`, not default home dir.
- Keep Ollama localhost-only.
- Keep wrapper-level redaction/path leak checks.

### Change next

1. Implement wrapper-owned batching over `index_vault({ mode: "incremental", paths: [...] })`.
2. Pre-filter every batch using wrapper protected/exclude policy before calling MCP.
3. Use small batches first; e.g. 10-25 files, then tune upward.
4. Store checkpoint JSON after each batch under `out/`.
5. Store batch stderr tail and parsed `[obsidian-semantic-mcp] index failed for ...` lines.
6. On timeout, write partial raw/sanitized report before cleanup.
7. Record actual candidate runtime versions (`node --version`, `npm --version`, candidate version) in reports.
8. Treat `dry_run` as diagnostic only: it does not exercise chunking/Ollama/SQLite writes.

## Mapping to current buglog

- BUG-001 full timeout: confirmed architecture issue; upstream has no progress/resume, so wrapper-owned batching is the correct fix.
- BUG-002 missing report on timeout: upstream will not help; must be fixed in our harness.
- BUG-003 missing file-level errors: upstream returns counts only; must parse stderr and preserve batch identity.
- BUG-004 protected `_Archive` rejection: confirmed explicit `paths` are resolved before per-file loop; wrapper must pre-filter.
- BUG-005 main probe lacks batched paths: confirmed `paths` is the correct upstream API to use.
- BUG-006 Node 24 ambiguity: confirmed `node:sqlite` makes Node 24 real; add explicit actual-runtime capture.

## Verdict

GO as guarded sandbox backend only.

NO-GO for raw direct live-vault exposure or full-vault monolithic indexing.

The next reliable path is not a stronger model and not isolating large files first. It is wrapper-owned batched/resumable indexing with protected-path prefiltering, partial reports, and stderr/error capture.
