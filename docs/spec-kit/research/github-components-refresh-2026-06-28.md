# GitHub components refresh — gh API only

- generated_at: `2026-06-28T05:22:57+00:00`
- source: `gh api` only; no generic web search, no clones, no token output.
- searched_buckets: `mcp_bridge, rag_graph, local_llm, markdown_memory`
- total_components_recorded: `37`

## Selected components fed into spec kit

|role|repo|stars|license|runtime|README/API signals|safety note|
|---|---|---:|---|---|---|---|
|primary_mcp_sandbox_candidate|cyanheads/obsidian-mcp-server|608|Apache-2.0|mcp-server|local, markdown, mcp, obsidian, rag, read, search, vault, write|evaluate in sandbox copy before live use; write-like capability mentioned; wrap as write-request/proposal-only; local-first/markdown/vault fit signal|
|knowledge_graph_pattern_reference|swarmclawai/swarmvault|588|MIT|knowledge-graph/memory-layer|graph, local, markdown, mcp, obsidian, ollama, rag, read, search, vault, write|evaluate in sandbox copy before live use; local-first/markdown/vault fit signal|
|primary_rag_graph_sandbox_candidate|benmaster82/Kwipu|255|MIT|rag-engine|graph, local, markdown, mcp, obsidian, ollama, rag, read, search, vault|evaluate in sandbox copy before live use; local-first/markdown/vault fit signal; check network/API/secret exposure before promotion|
|obsidian_local_ai_reference_candidate|takeshy/obsidian-local-llm-hub|50|MIT|obsidian-plugin/local-ai-hub|graph, local, markdown, mcp, obsidian, ollama, rag, read, search, vault|evaluate in sandbox copy before live use; write-like capability mentioned; wrap as write-request/proposal-only; local-first/markdown/vault fit signal; check network/API/secret exposure befor|
|secondary_mcp_sandbox_candidate|rps321321/obsidian-mcp-pro|24|MIT|mcp-server|graph, local, markdown, mcp, obsidian, ollama, rag, read, search, vault, write|evaluate in sandbox copy before live use; write-like capability mentioned; wrap as write-request/proposal-only; local-first/markdown/vault fit signal|
|agent_memory_pattern_reference|deeflect/dory|16|MIT|memory-layer|graph, local, markdown, mcp, obsidian, ollama, rag, read, search, write|evaluate in sandbox copy before live use; local-first/markdown/vault fit signal|
|python_mcp_reference_candidate|bettyguo/obsidian_mcp|8|MIT|mcp-server|graph, local, markdown, mcp, obsidian, rag, read, search, vault, write|evaluate in sandbox copy before live use; write-like capability mentioned; wrap as write-request/proposal-only; local-first/markdown/vault fit signal|

## Integration decisions

- Keep cyanheads/obsidian-mcp-server as primary MCP sandbox candidate; direct write tools must remain disabled/wrapped.
- Use benmaster82/Kwipu as primary Phase 04 RAG/graph sandbox candidate because it targets Markdown/Obsidian, wikilinks/YAML, hybrid retrieval, and local Ollama operation.
- Keep rps321321/obsidian-mcp-pro and bettyguo/obsidian_mcp as secondary MCP/API-shape references, not live write paths.
- Use swarmvault/dory/obsidian-local-llm-hub as pattern references for local-first memory/graph/agent integration; do not install into live vault in this slice.

## Full candidate table

|repo|stars|license|language|kind|buckets|selected|description|
|---|---:|---|---|---|---|---|---|
|cyanheads/obsidian-mcp-server|608|Apache-2.0|TypeScript|mcp-server|pinned_refresh|primary_mcp_sandbox_candidate|Read, write, search, and surgically edit Obsidian vault notes, tags, and frontmatter via MCP. STDIO or Streamable HTTP.|
|swarmclawai/swarmvault|588|MIT|TypeScript|knowledge-graph/memory-layer|pinned_refresh|knowledge_graph_pattern_reference|The local-first LLM Wiki: open-source knowledge graph builder, RAG knowledge base, and agent memory store. Built on Andrej Karpathy's pattern. An Obsidian alternative for personal knowledge |
|benmaster82/Kwipu|255|MIT|Python|rag-engine|pinned_refresh|primary_rag_graph_sandbox_candidate|Ask questions across your Markdown notes using a fully local Graph RAG engine. Built for Obsidian vaults, works with any folder of Markdown files. Extracts entity-relation triples from wikil|
|takeshy/obsidian-local-llm-hub|50|MIT|TypeScript|obsidian-plugin/local-ai-hub|pinned_refresh|obsidian_local_ai_reference_candidate|All-in-one local AI hub for Obsidian — LLM chat with vault tools, MCP servers, RAG, workflow automation, encryption, and edit history. Fully private, no cloud required.|
|rps321321/obsidian-mcp-pro|24|MIT|TypeScript|mcp-server|pinned_refresh|secondary_mcp_sandbox_candidate|The most feature-complete MCP server for Obsidian vaults — 23 tools + 3 resources for search, read, write, tags, link analysis, graph traversal, and canvas. Also ships as an Obsidian plugin |
|deeflect/dory|16|MIT|Python|memory-layer|pinned_refresh|agent_memory_pattern_reference|One memory layer for every AI agent. Local-first, markdown source of truth, and CLI/HTTP/MCP native. Your agent forgot who you are. Again. Dory fixes that.|
|bettyguo/obsidian_mcp|8|MIT|Python|mcp-server|pinned_refresh|python_mcp_reference_candidate| MCP server + 7 Claude skills for Obsidian vaults — read, search, write, and link notes from Claude / Cursor / ChatGPT. Filesystem-direct, local-first, round-trip safe.|
|mustbeperfect/definitive-opensource|3286|MIT|Python|github-component|local_llm, markdown_memory, rag_graph||The definitive list of the best of (consumer facing) open source.|
|noduslabs/infranodus-obsidian-plugin|152|AGPL-3.0|TypeScript|obsidian-plugin/graph-analysis|pinned_refresh||Advanced graph view for Obsidian: text analysis, topic modeling, and AI with InfraNodus AI text analysis tool: https://infranodus.com|
|rajudandigam/agent-inspect|95|MIT|TypeScript|local-ai-tool|markdown_memory||Local execution trees for TypeScript AI agents.  agent-inspect helps you understand what happened inside an AI agent run — locally. It turns manual steps, tool calls, LLM calls, structured l|
|jxzzlfh/awesome-stars|94|CC0-1.0|unknown|github-component|rag_graph|||
|Dicklesworthstone/frankenlibc|48|NOASSERTION|Rust|memory-layer|markdown_memory||Rust interposition layer for glibc: transparent safety membrane that incrementally replaces C library functions with memory-safe Rust implementations|
|griffinwork40/agent-afk|37|Apache-2.0|TypeScript|github-component|markdown_memory||Start a run in your terminal and walk away. Get pinged when it finishes, or needs you. Every step is a readable trace you check before anything ships.|
|smith-and-web/obsidian-mcp-server|17|MIT|TypeScript|mcp-server|pinned_refresh||MCP server for Obsidian vault management - enables Claude and other AI assistants to read, write, search, and organize your notes|
|chainlesschain/chainlesschain|8|NOASSERTION|JavaScript|github-component|local_llm, mcp_bridge, rag_graph|||
|linny006/llm-agents-radar|4|NOASSERTION|Python|local-ai-tool|rag_graph||Live-updating index of LLM agent frameworks shipping on GitHub, refreshed every 15 minutes|
|strikersam/autonomous-ai-agency|4|NOASSERTION|Python|mcp-server|local_llm, mcp_bridge||Autonomous AI Agent Infrastructure Platform — OpenAI-compatible AI gateway with MCP support, multi-agent orchestration, tool calling, observability, memory, RAG, AI workflows, and unified in|
|maqibg/Stargazer|3|NOASSERTION|unknown|github-component|local_llm, rag_graph|||
|Collinstudied660/mcp-hub|1|MIT|Python|mcp-server|mcp_bridge||Build and use production-ready MCP servers for Claude, Cursor, Windsurf, and more with one-line install and ready-to-run tools|
|linny006/rag-radar|1|NOASSERTION|Python|rag-engine/graph-tool|rag_graph||Live tracker of new RAG implementations, tools, and patterns — updated every 15 minutes|
|addxiaoyi/FullADDMAX-mcp|0|MIT|Python|mcp-server|mcp_bridge||Multi-agent MCP server: 4 mega tools / 31 ops, LLM autodetect (Claude/Cursor/Ollama), zero-config offline stub mode, one-command SVG panel. v0.6.0|
|AI-Nurse-Solutions/ai-operating-system-heart-of-a-nurse|0|NOASSERTION|Python|github-component|mcp_bridge|||
|anarion80/awesome-from-stars|0|NOASSERTION|Python|github-component|markdown_memory|||
|Andre151989/obsidian-lilbee|0|NOASSERTION|TypeScript|github-component|local_llm||Enhance Obsidian search by indexing deleted files to keep them visible and searchable within your vault.|
|Ansellwaxlike187/cowork-semantic-search|0|AGPL-3.0|Python|mcp-server|mcp_bridge||Search your local documents with semantic search in any MCP client, no API keys, no cloud access|

## Acceptance mapping

- Phase 03 MCP adapter remains `cyanheads/obsidian-mcp-server`; secondary MCP candidates are references only until sandboxed.
- Phase 04 RAG/graph adapter should evaluate `benmaster82/Kwipu` first, with output normalized to finding JSON and no live writes.
- Any component mentioning write/edit/delete/move stays behind `direct_write_enabled=false` and proposal-only wrapping.

Machine-readable bundle: `/home/hermesadmin/work/obsidian-operating-layer/docs/spec-kit/research/github-components.json`
