# Architecture — Obsidian Operating Layer

## Shape

Obsidian Operating Layer is a read-only-first control plane around an Obsidian vault.

```text
observe → propose → review → explicit approval → backup → apply → verify
```

## Components

| Component | Role |
|---|---|
| Vault | Human memory/source content; protected by default. |
| Observe tools | Read vault/repo state and produce evidence. |
| Proposal tools | Convert observations into dry-run proposal bundles. |
| Apply tool | The only live mutation path; requires approval manifest. |
| Verify tools | Check proposal/apply consistency and drift. |
| Hermes | Orchestrates, verifies, accepts/rejects. |
| Codex | Implements/reviews bounded repo tasks. |
| Nanobot | Read-only/proposal/report worker. |
| External adapters | MCP/RAG/Graphify/renderers; read/analyze/render/propose only. |

## Live mutation boundary

Only `tools/obsidian_apply.py` may perform live vault mutation, and only with an explicit approval manifest, backup target, expected hashes/targets, and post-apply verification.

## Detailed source specs

- `docs/spec-kit/03-safety-contract.md`
- `docs/spec-kit/05-final-desired-architecture.md`
- `docs/spec-kit/30-orchestrator-operating-spec.md`
- `docs/spec-kit/31-operator-flow-and-review-queue.md`
