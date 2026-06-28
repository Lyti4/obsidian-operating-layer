# Adapter Contracts

## Purpose

Adapters connect ready external components to Obsidian Operating Layer without giving them direct live-write authority.

## Non-negotiable rule

```text
external component output -> normalized finding/proposal -> obslayer safety gate -> approved apply
```

No adapter may directly create, modify, move, merge, or delete live vault files.

## Adapter metadata schema

```json
{
  "name": "cyanheads-obsidian-mcp-server",
  "kind": "mcp-server|obsidian-plugin|rag-engine|diagram-renderer|local-cli",
  "source": {
    "type": "github|obsidian-community-registry|local",
    "id": "owner/repo-or-plugin-id",
    "url": "https://github.com/owner/repo"
  },
  "license": "MIT|Apache-2.0|AGPL-3.0|unknown",
  "runtime": "node|python|obsidian|binary|java|docker",
  "capabilities": ["read", "search", "graph", "metadata-read", "propose", "render"],
  "forbidden_capabilities": ["write-direct", "delete-direct", "move-direct", "secret-read"],
  "direct_write_enabled": false,
  "vault_scope": "sandbox-copy|read-only-live|approved-output-only",
  "outputs": ["finding-json", "proposal-json", "markdown-report", "diagram-source", "pdf"],
  "risk_level": "low|medium|high",
  "risk_notes": [],
  "verification": {
    "sandbox_command": "...",
    "expected_outputs": []
  }
}
```

## Capability definitions

| Capability | Meaning | External allowed |
|---|---|---:|
| `read` | read markdown and safe metadata | yes |
| `search` | text/BM25/vector search | yes |
| `graph` | backlinks, wikilinks, clusters | yes |
| `metadata-read` | frontmatter/tag read | yes |
| `propose` | produce suggested changes | yes |
| `render` | render diagrams/PDF under output dir | yes |
| `write-request` | describe desired write as request | yes, converted to proposal |
| `write-direct` | filesystem write to live vault | no |
| `delete-direct` | delete live vault files | no |
| `move-direct` | move/rename live vault files | no |
| `secret-read` | read tokens/keys/.env | no |

## Adapter behavior by type

### Read/search adapters

Must operate read-only, return normalized outputs, avoid changing vault content, and record source paths/timestamps where available.

### Graph/RAG adapters

May produce backlinks, orphan notes, duplicates, candidate MOCs, related notes, and memory maps. They must keep output traceable to source notes and never auto-apply structural changes.

### Proposal adapters

Must separate suggestion from execution. They convert findings into obslayer proposal format with target paths, change type, risk level, rationale, and evidence.

### Render adapters

Must emit reproducible source artifacts first and write generated SVG/PDF only to safe output locations such as `out/diagrams/` or `out/reports/`.

## Output normalization

Every adapter must emit one of:

- `finding.json` — facts and observations;
- `proposal.json` — suggested changes in obslayer proposal shape;
- `report.md` — human-readable summary;
- `diagram.*` — source diagram or generated artifact under `out/reports/`.

Minimum finding shape:

```json
{
  "adapter": "component-name",
  "vault_root": "/home/hermesadmin/Obsidian",
  "generated_at": "ISO-8601",
  "findings": [
    {
      "type": "orphan-note|candidate-link|duplicate|metadata-issue|diagram",
      "path": "relative/path.md",
      "confidence": 0.0,
      "evidence": [],
      "suggested_action": "none|link|merge|move|format|render"
    }
  ]
}
```

Recommended run output shape:

```json
{
  "adapter": "graph-worker",
  "run_id": "run-20260628-001",
  "status": "ok",
  "findings": [],
  "artifacts": {
    "report": "out/reports/example.md",
    "proposal": "out/proposals/example.json",
    "diagram_source": "out/diagrams/example.mmd"
  },
  "write_requests": [],
  "warnings": [],
  "verification": {
    "sandboxed": true,
    "direct_write_disabled": true
  }
}
```

## Machine-readable schema

- `schemas/adapter-metadata.schema.json` defines the adapter metadata contract.
- `direct_write_enabled` is constrained to `false`.
- Forbidden mutation and secret capabilities are explicit enum values.

## Adapter acceptance checklist

- README/license reviewed.
- Direct writes disabled or sandboxed.
- Runs against copied test vault first.
- Outputs are deterministic enough to diff.
- Findings can be converted to proposal/report.
- Protected paths are excluded.
- No secrets are read, logged, or written.
