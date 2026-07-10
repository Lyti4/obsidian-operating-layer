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
| Apply tool | The only existing-note content-edit path; requires approval manifest. |
| Backfill report | Creates one new approved report and refuses overwrite. |
| Verify tools | Check proposal/apply consistency and drift. |
| Hermes | Orchestrates, verifies, accepts/rejects. |
| Codex | Implements/reviews bounded repo tasks. |
| Nanobot | Project-wide read-only/proposal observer. |
| External adapters | MCP/RAG/Graphify/renderers; read/analyze/render/propose only. |

## Live write boundaries

- Existing note edits pass only through `tools/obsidian_apply.py` with an exact
  approval manifest, backup target, expected hashes/targets and post-verify.
- `tools/obsidian_backfill_report.py` may create one explicitly approved new
  file inside resolved `--reports-dir`; it refuses path escape and overwrite and
  follows `docs/runbooks/obsidian_backfill_report.md`.
- External adapters, semantic tools and agents never inherit either authority.

Tool modes and exact write surfaces are canonical in `docs/tools/INDEX.md`.
Current service/job state is canonical only in `docs/RUNTIME_STATUS.md`.

## Detailed source specs

- `docs/spec-kit/03-safety-contract.md`
- `docs/spec-kit/05-final-desired-architecture.md`
- `docs/spec-kit/30-orchestrator-operating-spec.md`
- `docs/spec-kit/31-operator-flow-and-review-queue.md`

These numbered specs are preserved design sources. Active feature work is
selected by `.specify/feature.json` under `specs/`.
