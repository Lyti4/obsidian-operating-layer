# Worker Orchestration Spec

## Workers

- `plugin-scout`: reads Obsidian community plugin registry and GitHub metadata.
- `mcp-reader`: connects to selected MCP server in read-only mode.
- `graph-worker`: builds links/backlinks/orphans/candidate MOCs using plugin/RAG outputs.
- `retrieval-worker`: BM25/vector/hybrid search via ready engine where available.
- `lint-worker`: invokes Obsidian Linter-compatible rules or reports required fixes.
- `proposal-worker`: converts all findings into obslayer proposal JSON/Markdown.
- `report-worker`: writes reports and mini-base notes under approved Reports/project paths.

## Queue shape

```json
{
  "task_id": "obslayer-...",
  "worker": "graph-worker",
  "capabilities": ["read", "search", "propose"],
  "vault_root": "/home/hermesadmin/Obsidian",
  "inputs": {},
  "outputs": {"proposal": "...", "report": "..."},
  "write_policy": "proposal_only"
}
```

## Capability rule

- `read`: ok for external components.
- `search`: ok for external components.
- `graph`: ok for external components.
- `propose`: ok for external components.
- `write-request`: must become obslayer proposal.
- `write-direct`: forbidden except obslayer apply with manifest.
