# Safety Contract

## Non-negotiable

- dry-run by default;
- no live writes from community plugins/MCP/RAG engines;
- no secrets/tokens printed or stored in notes;
- protected paths are immutable: `.obsidian`, `_Backups`, `_Archive`, `.trash`, Soul-protected areas;
- proposal targets must match approval manifest targets 1:1;
- backups before live write;
- post-verify after live write.

## External component adapter contract

Every adapter must expose:

```json
{
  "name": "component-name",
  "source": "github/plugin-registry/local",
  "capabilities": ["read", "search", "graph", "propose"],
  "direct_write_enabled": false,
  "license": "...",
  "risk_notes": []
}
```
