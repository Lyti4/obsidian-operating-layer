# GitHub API Refresh — Obsidian Knowledge Indexing Tools

Date: 2026-06-28  
Method: authenticated GitHub REST API via `gh api search/repositories` plus README fetch via `gh api repos/*/readme`; no web search.  
Raw artifacts:

- `/home/hermesadmin/work/obsidian-operating-layer/out/github-indexing-search-20260628.json`
- `/home/hermesadmin/work/obsidian-operating-layer/out/github-indexing-deep-search-20260628.json`

Unique repositories seen after deep refresh: 38  

## Search queries

### Initial
- `obsidian mcp vector search`
- `obsidian semantic search mcp`
- `obsidian ollama embeddings search`
- `markdown vault mcp fts5 semantic`
- `markdown vector search mcp`
- `obsidian graph rag mcp`
- `obsidian smart connections mcp`
- `obsidian local rest api mcp`
- `topic:obsidian-plugin semantic search embeddings`
- `topic:mcp-server obsidian markdown vault`
- `obsidian RAG markdown Ollama MCP`
- `sqlite fts5 markdown mcp`

### Additional targeted refresh
- `"no write tools" obsidian mcp`
- `"SQLite FTS5" "Obsidian" MCP`
- `"sqlite-vec" obsidian MCP`
- `"local Ollama embeddings" Obsidian MCP`
- `"frontmatter-aware" markdown MCP`
- `"incremental reindex" markdown MCP`
- `"Smart Connections" MCP Obsidian`
- `"Obsidian" "Graph RAG" Ollama`
- `"vault" "FTS5" "MCP server" markdown`
- `"Obsidian" "read-only" "semantic retrieval" MCP`

## Highest-priority candidates

| Repository | Stars | Lang | License | Updated | Why relevant |
|---|---:|---|---|---|---|
| `DalecB/obsidian-semantic-mcp` | 0 | JavaScript | MIT | 2026-06-03 | Read-only semantic retrieval MCP for Obsidian vaults. Local Ollama embeddings, SQLite FTS5, no write tools. |
| `pvliesdonk/markdown-vault-mcp` | 18 | Python | MIT | 2026-06-27 | Generic markdown collection MCP server with FTS5 + semantic search, frontmatter-aware indexing, and incremental reindexing |
| `benmaster82/Kwipu` | 255 | Python | MIT | 2026-06-25 | Ask questions across your Markdown notes using a fully local Graph RAG engine. Built for Obsidian vaults, works with any folder of Markdown files. Extracts entity-relation triples from wikilinks & YAML frontmatter, retrieves answers via hybrid search (vector + BM25 + temporal). Multilingual. No cloud. Runs on Ollama. |
| `Gustav-Proxi/cortex` | 0 | Swift | Apache-2.0 | 2026-06-09 | Local-first MCP server giving any LLM client semantic + literal search and full read/write over an Obsidian/markdown vault. Local embeddings via Ollama, sqlite-vec index. |
| `jacksteamdev/obsidian-mcp-tools` | 18 | Python | MIT | 2026-06-27 | Add Obsidian integrations like semantic search and custom Templater prompts to Claude or any MCP client. |
| `coddingtonbear/obsidian-local-rest-api` | 2540 | TypeScript | MIT | 2026-06-28 | A secure REST API and Model Context Protocol (MCP) server for your vault. |
| `dan6684/smart-connections-mcp` | 6 | - | NOASSERTION | 2026-06-25 | MCP server that exposes Obsidian Smart Connections vector database to Claude Code via semantic search |
| `Epistates/turbovault` | 132 | Rust | MIT | 2026-06-24 | Markdown and OFM SDK w/ MCP server that transforms your Obsidian vault into an intelligent knowledge system |
| `ngmeyer/librarian-mcp` | 9 | Rust | MIT | 2026-06-01 | The Karpathy LLM Wiki pattern, productionized. MCP server that gives Claude a librarian for your Obsidian vault — graph traversal, auto-wikilinks, trigram search. |
| `Detective-XH/DocGraph` | 3 | Go | MIT | 2026-06-15 | Govern your documents like code. MCP server that indexes .md/.docx/.html/.pdf into a SQLite knowledge graph and runs drift audits — stale policies, conflicting research claims, superseded docs, undocumented code exports. 12 MCP tools incl. cross-reference graph, governance + provenance metadata, topic similarity. Single binary, zero runtime deps. |
| `roomi-fields/rtfm` | 16 | Python | MIT | 2026-06-28 | The open retrieval layer for AI coding agents. Indexes code, docs, legal, research, data — 22 parsers (incl. EPUB, DOCX, ODT), FTS5 + semantic search, knowledge graph. Serves surgical context via MCP. Open source, local, free. |
| `uhop/vault-storage` | 0 | Python | - | 2026-06-05 | AI-agent-first knowledge base over markdown. SQLite + sqlite-vec for fast lookup, semantic search, and typed-edge traversal; BGE embeddings; REST server (MCP planned). |
| `jagoff/memo` | 0 | Python | MIT | 2026-06-28 | Persistent semantic memory for AI agents — 100% local on Apple Silicon (MLX). Markdown source of truth + sqlite-vec hybrid search, with an MCP server and CLI. No cloud, no keys. |

## README/static review highlights

### `DalecB/obsidian-semantic-mcp`
- README status: ok
- Keyword flags: write, delete, move, create, patch, cloud, ollama, sqlite, fts5, vector, mcp, read-only, incremental
- `<h1 align="center">Obsidian Semantic Search MCP</h1>`
- `Read-only semantic retrieval for agents that need to find the right Obsidian note without write access.`
- `<a href="https://www.npmjs.com/package/@dalecb/obsidian-semantic-mcp"><img alt="npm" src="https://img.shields.io/npm/v/@dalecb/obsidian-semantic-mcp?color=111827"></a>`
- `<a href="https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.DalecB/obsidian-semantic-mcp"><img alt="MCP Registry" src="https://img.shields.io/badge/MCP%20Registry-active-111827"></a>`
- `local Obsidian vault -> read-only scanner -> local SQLite index -> MCP search/read tools`

### `pvliesdonk/markdown-vault-mcp`
- README status: ok
- Keyword flags: write, delete, move, create, patch, openai, ollama, sqlite, fts5, vector, mcp, frontmatter, incremental
- `A generic markdown vault [MCP](https://modelcontextprotocol.io/) server with FTS5 full-text search, semantic vector search, frontmatter-aware indexing, incremental reindexing, and non-markdown attachment support.`
- `Point it at a directory of Markdown files (an Obsidian vault, a docs folder, a Zettelkasten, a PARA vault) and it exposes search, read, write, and edit tools over the Model Context Protocol.`
- `- **Full-text search** — SQLite FTS5 with BM25 scoring, porter stemming`
- `- **Semantic search** — cosine similarity over embedding vectors (FastEmbed, Ollama, or OpenAI)`
- `- **Hybrid search** — Reciprocal Rank Fusion combining FTS5 and vector results`

### `benmaster82/Kwipu`
- README status: ok
- Keyword flags: delete, create, cloud, ollama, vector, mcp, frontmatter, incremental
- `[![Ollama](https://img.shields.io/badge/LLM-Ollama-orange.svg)](https://ollama.ai/)`
- `[![MCP Server](https://img.shields.io/badge/MCP-compatible-blue.svg)](https://modelcontextprotocol.io/)`
- `- **MCP Server** - use Kwipu as a tool inside Claude Desktop, Cursor, Windsurf, or any MCP-compatible agent. All processing runs locally via Ollama.`
- `- **Incremental updates** - editing a note no longer rebuilds the entire graph. Modified files are updated in-place in seconds.`
- `- **Startup validation** - checks that Ollama is running and models are available before starting. Clear error messages with suggested commands.`

### `coddingtonbear/obsidian-local-rest-api`
- README status: ok
- Keyword flags: write, delete, move, create, patch, mcp, frontmatter
- `Access your vault through the **REST API** or the **built-in [MCP server](https://modelcontextprotocol.io/)** — both interfaces expose the same core capabilities, so scripts, browser extensions, and AI agents all speak the same language.`
- `- **Read, create, update, or delete notes** — full CRUD on any file in your vault, including binary files`
- `- **Surgically patch specific sections** — target a heading, block reference, or frontmatter key and append, prepend, or replace just that section without touching the rest of the file`
- `- **Search your vault** — simple full-text search or structured [JsonLogic](https://jsonlogic.com/) queries against note metadata (frontmatter, tags, path, content)`
- `- **Access the active file** — read or write whatever note is currently open in Obsidian`

### `jacksteamdev/obsidian-mcp-tools`
- README status: ok
- Keyword flags: create, mcp
- `2. A local MCP server that handles communication with AI applications`
- `- **Semantic Search**: AI assistants can search your vault based on meaning and context, not just keywords [^5]`
- `- [Smart Connections](https://smartconnections.app/) plugin for semantic search capabilities`
- `4. Click "Install Server" to download and configure the MCP server`
- `- Download the appropriate MCP server binary for your platform`

### `dan6684/smart-connections-mcp`
- README status: decode_error Invalid base64-encoded string: number of data characters (8357) cannot be 1 more than a multiple of 4
- Keyword flags: -

### `Epistates/turbovault`
- README status: decode_error Incorrect padding
- Keyword flags: -

### `ngmeyer/librarian-mcp`
- README status: ok
- Keyword flags: write, create, cloud, mcp, frontmatter
- `> **Runs entirely locally.** Your vault data never leaves your machine. Librarian reads and writes files on disk and communicates with Claude over stdio. No network calls, no telemetry, no cloud storage.`
- ``--setup` writes the MCP server config into Claude Desktop and Claude Code (with backups), and installs the `/librarian` skill so you get 12 slash commands out of the box.`
- `| Auto-wikilinks on write | No | No | No | **Yes** |`
- `| `library_write` | Write a file with auto-wikilink detection |`
- `| `library_metadata` | Read YAML frontmatter from a file |`

### `Gustav-Proxi/cortex`
- README status: ok
- Keyword flags: write, delete, move, create, patch, cloud, ollama, sqlite, vector, mcp, frontmatter, incremental
- `**The local-first brain for your notes — one MCP server that gives every LLM client your entire Obsidian vault.**`
- `[![MCP server](https://img.shields.io/badge/MCP-server-7C3AED?style=flat-square)](#connect-it-to-an-mcp-client)`
- `[![Embeddings: Ollama](https://img.shields.io/badge/embeddings-Ollama-000000?style=flat-square&logo=ollama&logoColor=white)](https://ollama.com)`
- `[![Vectors: sqlite-vec](https://img.shields.io/badge/vectors-sqlite--vec-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://github.com/asg017/sqlite-vec)`
- `- 🔎 **Search** — semantic (local embeddings), literal (grep), and **hybrid** (keyword ⊕ vector); plus frontmatter/property filters and the `[[wikilink]]` graph (`backlinks` / `outgoing_links`).`

### `Detective-XH/DocGraph`
- README status: ok
- Keyword flags: write, delete, move, create, patch, openai, sqlite, fts5, mcp, frontmatter, incremental
- `### Documentation knowledge graph MCP server for LLM agents`
- `**MCP-native for LLM agents · CJK + Latin FTS5 · Multi-format graph**`
- `Your `.docx` / `.pdf` / `.html` archive has no frontmatter, so it can't be governed. DocGraph fixes that without compromising authority:`
- `- **CJK + Latin search that actually works** — FTS5 trigram, not English-only`
- `- **Workspace fan-out** — one MCP server, N projects, one query`

### `roomi-fields/rtfm`
- README status: decode_error Incorrect padding
- Keyword flags: -

## Screening notes

### Strong fit

- `DalecB/obsidian-semantic-mcp`: description matches our target almost exactly: read-only semantic retrieval, local Ollama embeddings, SQLite FTS5, no write tools. It is very new and zero-star, so static code review is mandatory before sandbox use.
- `pvliesdonk/markdown-vault-mcp`: headless markdown vault MCP with FTS5, semantic search, frontmatter and incremental reindexing. It exposes write/edit tools per README, so it is a strong candidate only behind read-only configuration or a strict tool filter.
- `benmaster82/Kwipu`: more visible local Markdown/Obsidian Graph RAG candidate with Ollama/MCP/BM25+vector direction. Strong second sandbox spike candidate.

### Useful but needs safety wrapping

- `coddingtonbear/obsidian-local-rest-api`: mature and popular, but REST/MCP can expose write/patch behavior; only safe behind strict read-only config or proposal-only wrapper.
- `jacksteamdev/obsidian-mcp-tools`: active Obsidian MCP tooling with semantic search; review exposed tools before agent access.
- `dan6684/smart-connections-mcp`: useful if we use Smart Connections as the Obsidian-native index; still depends on plugin state.
- `Gustav-Proxi/cortex`: interesting sqlite-vec/Ollama design, but explicitly advertises full read/write; not direct-safe.

### Broader watchlist

- `Epistates/turbovault`, `ngmeyer/librarian-mcp`, `Detective-XH/DocGraph`, `roomi-fields/rtfm`, `uhop/vault-storage`, `jagoff/memo` are useful patterns for graph/search/provenance/local agent memory, but not first integration targets.

## Deep static review results

### `DalecB/obsidian-semantic-mcp`

Verdict: **primary sandbox spike target**.

- MCP tools: `search_notes`, `read_note`, `index_vault`, `index_status`.
- Vault mutation surface: no write/delete/move tools found; `index_vault` mutates only derived SQLite state.
- Storage: local SQLite (`meta`, `notes`, `chunks`, `chunks_fts`) with heading-based chunks and line ranges.
- Embeddings: Ollama (`bge-m3` default) through `OLLAMA_BASE_URL`; require localhost-only policy.
- Protected paths: strongest reviewed guard set, including `.obsidian`, hidden folders, `.smart-env`, `.claude`, `.codex-*`, user excludes, realpath/traversal/symlink checks.
- Provenance: matched sections include heading, lines, snippet, reason; `read_note` supports line ranges.
- Risks: Node >=24 while current host has Node 22; young project with low ecosystem signal; no lockfile; stale index possible after policy changes until full reindex.
- Review evidence: tests passed in static review (`npm test` 19/19).

### `pvliesdonk/markdown-vault-mcp`

Verdict: **secondary candidate only behind read-only wrapper/tool filter**.

- Strengths: mature Python project, FTS5 + vector sidecar + frontmatter + graph tools + incremental reindex.
- Mutation surface: exposes `write`, `edit`, `delete`, `rename`, `move_folder`, `fetch`, `git_sync`, upload links.
- Read-only support exists, but Operating Layer must independently filter tools and reject mutation paths.
- Embeddings: FastEmbed/Ollama local, but OpenAI/OpenAI-compatible env config is available and must be disabled by policy.
- Protected paths: configurable excludes, but not as strong as a built-in invariant unless config is correct.
- Provenance: path/heading/start_line/content/etag style metadata; not a strict span/citation model by default.
- Risks: destructive folder moves, server-side fetch surface, git managed mode, remote debug docs, cloud embedding config.

### `benmaster82/Kwipu`

Verdict: **experimental graph-RAG comparison spike, not base integration target**.

- MCP tools: single `query_graph(question)` tool; no MCP write/delete/move.
- Storage: LlamaIndex `PropertyGraphIndex` persisted under local storage; watcher-driven updates; file hashes.
- Retrieval: wikilinks/frontmatter extraction, LLM path extraction, vector/BM25/temporal/metadata hybrid retrieval.
- Embeddings: Ollama local by code path, but README/default model workflow can point to cloud-capable Ollama models.
- Protected paths: excludes `.obsidian`, but lacks rich protected-path policy.
- Provenance: prompt asks for cited filenames, but MCP returns string and does not expose source spans.
- Risks: no tests/CI found, monolithic implementation, auto-watcher mutations of derived storage, weak provenance.

## Final Codex-reviewed recommendation

- Start with `DalecB/obsidian-semantic-mcp` in sandbox as the safest read-only spike.
- Keep durable architecture as **SQLite FTS5 + graph catalog first, semantic sidecar second**.
- Treat `pvliesdonk/markdown-vault-mcp` as a powerful fallback only after strict tool filtering.
- Treat `Kwipu` as quality/reference comparison for Graph RAG, not live integration base.
- Store index artifacts in rebuildable storage under `out/` for evaluation; never inside the source vault.
- Preserve the existing Operating Layer mutation boundary: `observe → propose → review → dry-run → approval → backup → apply → verify`.

## Recommended shortlist for spike

1. Sandbox run: `DalecB/obsidian-semantic-mcp` with local-only Ollama and no-write acceptance tests.
2. Fallback sandbox run: `pvliesdonk/markdown-vault-mcp` with read-only mode plus host-side tool filter.
3. Comparison sandbox run: `benmaster82/Kwipu` for Graph RAG quality only.
4. Optional controlled-transport review: `coddingtonbear/obsidian-local-rest-api`.

## Verification performed

- GitHub search used `gh api`; no browser/web search used.
- README/static metadata fetched through GitHub API for 11 candidates.
- Machine-readable deep result stored under `out/` and copied into docs JSON.
- No tokens or credentials are stored in this report.
