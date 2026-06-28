# Phase 04 RAG/graph adapter sandbox evaluation

- timestamp: `20260628-052858Z`
- adapter: `benmaster82/Kwipu`
- adapter record: `docs/spec-kit/research/sample-adapter-records/benmaster82-kwipu.json`
- sandbox source: `/home/hermesadmin/work/obsidian-operating-layer/out/sandbox-sources/ool-phase04-rag-graph-demo`
- sandbox copy: `/home/hermesadmin/work/obsidian-operating-layer/out/sandbox-vaults/rag-kwipu-demo`
- JSON report: `/home/hermesadmin/work/obsidian-operating-layer/out/reports/ool-phase04-rag-graph-adapter/rag-graph-evaluation-benmaster82-Kwipu-20260628-052858Z.json`
- Markdown report: `/home/hermesadmin/work/obsidian-operating-layer/out/reports/ool-phase04-rag-graph-adapter/rag-graph-evaluation-benmaster82-Kwipu-20260628-052858Z.md`
- out/docs JSON report: `/home/hermesadmin/work/obsidian-operating-layer/out/docs/ool-phase04-rag-graph-adapter/rag-graph-evaluation-benmaster82-Kwipu-20260628-053154Z.json`
- out/docs Markdown report: `/home/hermesadmin/work/obsidian-operating-layer/out/docs/ool-phase04-rag-graph-adapter/rag-graph-evaluation-benmaster82-Kwipu-20260628-053154Z.md`

## Scope

This slice evaluates the adapter wrapper and normalized finding schema only. It does not install Kwipu, index a live vault, call Ollama, or mutate Obsidian content. The wrapper treats the ready component as a sandbox-only RAG/graph adapter and normalizes graph observations into proposal-compatible finding records.

## Commands

```bash
python3 tools/obsidian_sandbox.py \
  --source-vault /home/hermesadmin/work/obsidian-operating-layer/out/sandbox-sources/ool-phase04-rag-graph-demo \
  --sandbox-root out/sandbox-vaults \
  --name rag-kwipu-demo \
  --reset \
  --out out/reports/ool-phase04-rag-graph-adapter/sandbox-copy.json

python3 tools/obsidian_rag_graph_adapter.py \
  --adapter-record docs/spec-kit/research/sample-adapter-records/benmaster82-kwipu.json \
  --sandbox-vault out/sandbox-vaults/rag-kwipu-demo \
  --out-dir out/reports/ool-phase04-rag-graph-adapter

python3 tools/obsidian_rag_graph_adapter.py \
  --adapter-record docs/spec-kit/research/sample-adapter-records/benmaster82-kwipu.json \
  --sandbox-vault out/sandbox-vaults/rag-kwipu-demo \
  --out-dir out/docs/ool-phase04-rag-graph-adapter
```

## Normalized findings observed in sandbox

- `nonexistent-link`: `Projects/Obsidian Operating Layer` links to `Missing Proposal Normalizer`.
- `orphan-note`: `Inbox Capture` has no inbound or outbound wikilinks.
- `moc-candidate`: clusters for `architecture`, `automation`, `obslayer`, and `safety`.
- `candidate-backlink`: architecture notes share tags but are not linked.
- `graph-summary`: 4 markdown notes scanned, 4 wikilinks resolved.

Every write-like result is recorded as proposal-only (`proposal_required=true`, `executed=false`).

## Verification

```json
{
  "direct_write_disabled": true,
  "normalized_findings_only": true,
  "notes_scanned": 4,
  "proposal_only_for_write_like_suggestions": true,
  "sandboxed": true
}
```

## Promotion decision

Keep `benmaster82/Kwipu` as the primary Phase 04 ready-component candidate, but promote only the adapter contract and normalized finding schema now. A future live-like sandbox may install/run Kwipu against a copied vault and map its native outputs into this schema; live vault writes remain out of scope.
