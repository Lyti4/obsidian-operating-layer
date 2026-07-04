# Graphify → Nanobot → Embedding orchestration spec

## Purpose

This spec is the current orchestration contract for the Obsidian Operating Layer semantic/indexing path. It separates responsibilities so embedding work is more accurate and safer: Graphify decides the bounded candidate set first, Nanobot reviews/operates only through packets, and the embedding runner embeds only the Graphify-derived manifest.

## Current assignment

| Layer | Assignee | Role | Writes allowed | Acceptance owner |
|---|---|---|---|---|
| Hermes | Hermes Agent | Orchestrator, safety gate, evidence reviewer, user-facing decision maker | Project docs/code/reports only after verification | Hermes |
| Graphify | Graphify native workflow | Build/query/explain graph on sandbox snapshots; produce graph artifacts and candidate source set | `graphify-out/`, reports under `out/` | Hermes |
| Nanobot | Restricted Nanobot worker | Review bounded packets, summarize evidence, propose fixes, request missing context | Its workspace packet `REPORT.md`; archived by Hermes | Hermes |
| Embedding runner | `tools/obsidian_graphify_embedding_run.py` | Embed only manifest candidates, per bounded chunk, derived cache only | `out/external-indexing-spike/graphify-derived/` and `out/reports/graphify-embedding-runs/` | Hermes |

## Canonical pipeline

```text
sandbox snapshot
  ↓
Graphify extract / cluster / query-path-explain
  ↓
graphify-out/graph.json + GRAPH_REPORT.md
  ↓
Graphify-derived embedding handoff
  ↓
out/reports/graphify-embedding-handoff/.../embedding-manifest.json
  ↓
Nanobot packet review, if code/workflow changed
  ↓
bounded embedding runner reads manifest only
  ↓
derived embedding cache + embedding-run report
  ↓
Hermes acceptance; no live apply without separate approval manifest
```

## Accuracy rationale

This is expected to be better and more precise than raw-first embedding because:

1. Graphify removes broad vault crawling from the embedding decision path.
2. Candidates are traceable to Graphify nodes, communities, degree/score, source paths, and hashes.
3. The runner rejects stale hashes, missing files, protected paths, path escapes, non-sandbox roots, and live-vault paths.
4. Embeddings happen per chunk, not per whole large note, avoiding earlier oversized chunk failures.
5. Derived cache records provenance, chunk counts, token counts, dimensions, truncation state, and provider/model.

## Graphify contract

Graphify is responsible for graph production and graph-aware selection, not for direct vault mutation.

Required evidence:

- named sandbox under `out/sandbox-vaults/<name>`;
- `.graphifyignore` / protected path policy;
- `graphify-out/graph.json`;
- `graphify-out/GRAPH_REPORT.md` when available;
- any `graphify query`, `graphify path`, or `graphify explain` prompts that influenced selection;
- confirmation that no live vault mutation and no embedding auto-run occurred.

If semantic Graphify routing is unavailable, Graphify may run only an explicitly labeled structural/local degraded pass and must not make semantic-model claims.

## Nanobot contract

Nanobot is assigned only by workspace-local packets. It must not be given broad filesystem access to compensate for missing evidence.

Allowed:

- read the packet;
- inspect sanitized copied evidence;
- write `REPORT.md` in the same packet;
- recommend `approve`, `approve-with-fixes`, or `reject`;
- request missing tools/evidence in the report.

Forbidden without explicit user approval:

- live vault mutation;
- direct apply;
- service restart;
- cron creation;
- auth/profile changes;
- secret reading/printing;
- paid/direct API-key fallback;
- automatic embeddings outside a runner packet.

Latest reviewed packet shape for this layer: `graphify-embedding-runner-review-...`, verdict `approve-with-fixes`; Hermes must verify fixes before accepting.

## Embedding handoff contract

The handoff entrypoint is:

```bash
python3 tools/obsidian_graphify_embedding_handoff.py   --graph-json out/reports/.../graphify-out/graph.json   --sandbox-vault out/sandbox-vaults/<name>   --out-dir out/reports/graphify-embedding-handoff/<run>   --derived-root out/external-indexing-spike/graphify-derived/<run>
```

It creates:

- `embedding-manifest.json`;
- `REPORT.md`.

The manifest is an allowlist. It must keep `embedding_policy.auto_execute=false`; it does not start embeddings.

## Bounded embedding runner contract

The runner entrypoint is:

```bash
python3 tools/obsidian_graphify_embedding_run.py   --manifest out/reports/graphify-embedding-handoff/<run>/embedding-manifest.json   --out-dir out/reports/graphify-embedding-runs/<run>   --derived-root out/external-indexing-spike/graphify-derived/<run>   --provider ollama   --ollama-base-url http://127.0.0.1:11434   --ollama-model bge-m3   --ollama-timeout-seconds 240   --max-chars-per-chunk 2000   --chunk-overlap 200   --max-files 25
```

Hard requirements:

- manifest-only input; no raw vault walk;
- sandbox under `out/sandbox-vaults/<name>` only;
- report under `out/reports/graphify-embedding-runs/` only;
- derived cache under `out/external-indexing-spike/graphify-derived/` only;
- local Ollama loopback only for real semantic embeddings;
- real semantic provider is `bge-m3` / `bge-m3:latest`;
- `local-hashing-v1` requires explicit `--allow-smoke-provider` and is smoke/test only, not semantic-quality;
- concurrency remains effectively `1`;
- checkpoint is written for audit/resume state;
- no live-vault mutation.

## Runtime gates

Current runtime services are production-like local surfaces. Do not silently restart them.

Before claiming a real semantic embedding run:

1. Verify Ollama is listening on `127.0.0.1:11434`.
2. Verify `bge-m3` is installed and advertises embedding capability.
3. Run a short `/api/embed` probe against loopback only.
4. Run one bounded manifest candidate with `--max-files 1` and chunk size `2000`.
5. Verify vector dimensions, chunk lengths, report paths, derived cache paths, and safety booleans.

If Ollama is down, status is `blocked-runtime`, not success. Offline tests may still pass with fake Ollama or explicit smoke provider.

## Acceptance checklist

For every full slice, Hermes records:

- Graphify artifact paths;
- embedding manifest path;
- Nanobot packet/report path if Nanobot was assigned;
- runner command or reason it was not run;
- provider/model and runtime health;
- processed/skipped counts;
- chunk count and max chunk size evidence;
- protected-path and secret-scan result;
- no live mutation / no direct apply / no cron / no restart / no auth/profile change;
- tests run and exact outcomes.

## Stop conditions

Stop and report if:

- manifest points outside `out/reports/graphify-embedding-handoff/`;
- sandbox is missing, live, bare `out/sandbox-vaults`, or outside `out/sandbox-vaults/<name>`;
- any candidate uses absolute paths, `..`, protected paths, or hash mismatch;
- derived/report output escapes approved `out/` roots;
- Ollama base URL is non-loopback;
- model is not `bge-m3`/`bge-m3:latest` for real semantic runs;
- secrets appear in outputs;
- any live vault file is touched.

## Current known blocker

After session shutdown, `127.0.0.1:11434`, `127.0.0.1:18790`, and `127.0.0.1:8787` were not listening. Real `bge-m3` acceptance remains blocked until the local runtime is intentionally brought up and smoked. This does not invalidate offline code/spec verification, but it prevents claiming a completed real semantic embedding pass.

## Current large-chunk Ollama behavior

The embedding runner may be started with larger chunks first, for example `--max-chars-per-chunk 6000`, to preserve more local semantic context when Ollama can handle it. The runner remains bounded by the Graphify-derived manifest and sandbox guardrails.

If a local Ollama chunk request fails because the chunk is too large, rejected, or times out, the runner can split that chunk inside the same file/manifest scope and retry smaller parts. This is a local degradation path only; it must not switch to an external embedding provider.

Accepted smoke evidence:

```text
python tools/obsidian_graphify_embedding_run.py \
  --manifest out/reports/graphify-embedding-handoff/bge-m3-smoke-20260703T050031Z/embedding-manifest.json \
  --out-dir out/reports/graphify-embedding-runs/orchestrator-bge-m3-bigchunk-smoke-20260703T0720Z \
  --max-files 2 \
  --provider ollama \
  --ollama-base-url http://127.0.0.1:11434 \
  --ollama-model bge-m3 \
  --max-chars-per-chunk 6000 \
  --chunk-overlap 300
# status=ok processed=2 skipped=0 dimensions=1024
```

Nanobot audit note: the post-fix Nanobot review attempt was made through `nanobot-headroom-agent`, but the provider failed with `refresh_token_reused`; this is an auth repair/switch class issue for Nanobot/Codex, not an embedding runner failure.


## Low-memory VPS runtime note

On the current small VPS, `bge-m3` can be OOM-killed by Ollama on larger chunks. The blessed local service is `ollama-hermes.service` with loopback-only host, `OLLAMA_MODELS=/home/hermesadmin/.ollama/models`, `OLLAMA_CONTEXT_LENGTH=512`, `OLLAMA_NUM_PARALLEL=1`, `OLLAMA_KEEP_ALIVE=30s`, and `OLLAMA_MAX_LOADED_MODELS=1`.

For acceptance on this host, use `--ollama-timeout-seconds 240` or higher and prefer `--max-chars-per-chunk 500` for real `bge-m3` smoke/medium batches unless memory is upgraded. If Ollama is OOM-killed, report `blocked-runtime/oom` rather than treating Headroom or Graphify as the cause.

## Accepted final468 sandbox pass — 2026-07-04

Hermes completed the first full Graphify-derived sandbox embedding pass for the current handoff set.

Evidence:

- embedding run report: `out/reports/graphify-embedding-runs/step468-final-safe-20260703T192852Z/REPORT.md`
- embedding run JSON: `out/reports/graphify-embedding-runs/step468-final-safe-20260703T192852Z/embedding-run.json`
- derived cache root: `out/external-indexing-spike/graphify-derived/step50-fixed-20260703T171829Z`
- query smoke report: `out/reports/graphify-embedding-query-smoke/final468-20260704T065635Z/REPORT.md`
- acceptance report: `out/reports/graphify-final468-acceptance-20260704T065729Z/REPORT.md`

Counts:

```text
records: 468 / 468
processed: 467
skipped: 1 empty/whitespace-only file
embedding sidecar files: 467
chunks indexed by query smoke: 3605
embedding sidecar files: 467
all JSON files in derived cache: 468
missing embedding files: 0
```

The skipped file was handled as `empty_text_after_truncation`; empty files must not be sent to Ollama and must not fail the run.

Semantic query smoke was run against the derived cache and returned plausible top hits for Obsidian link hygiene, Graphify corpus/cross-repo patterns, approval-manifest safety, and Nanobot/Headroom/Codex orchestration. This confirms the derived cache is queryable, not merely present on disk.

Runtime decision for this 4 GB VPS:

- Hot-mode (`--keep-ollama-loaded-after-run`) was tested and rejected for long series because zram filled too aggressively.
- Accepted mode on this host is safe batching: bounded `max_files`, `OLLAMA_NUM_PARALLEL=1`, automatic Ollama unload after each run, zram cleanup between large batches, and strict resource preflight before the next batch.
- `bge-m3` remains local-only through Ollama loopback; no external embedding provider is accepted by default.

Reusable query smoke entrypoint:

```bash
python3 tools/obsidian_graphify_embedding_query.py \
  --run-json out/reports/graphify-embedding-runs/<run>/embedding-run.json \
  --out-dir out/reports/graphify-embedding-query-smoke/<run> \
  --query "Obsidian Operating Layer safety boundary" \
  --query "approval manifest backup apply verify" \
  --provider ollama \
  --ollama-base-url http://localhost:11434 \
  --ollama-model bge-m3
```

Make target:

```bash
make graphify-embedding-query \
  GRAPHIFY_EMBED_QUERY_RUN_JSON=out/reports/graphify-embedding-runs/<run>/embedding-run.json \
  GRAPHIFY_EMBED_QUERY_REPORTS=out/reports/graphify-embedding-query-smoke/<run>
```

Acceptance boundary remains unchanged: this was a sandbox/handoff pass only. No live vault mutation is allowed from embedding/query results without a separate proposal, approval manifest, backup, apply, and verify cycle.

## Nanobot-first / Hermes-acceptance loop

For proposal-only Graphify/embedding follow-up work, use this sequence:

```text
Hermes prepares sanitized project packet under out/queue/<task-id>/
  ↓
Hermes copies the same packet into Nanobot's allowed workspace:
  /home/hermesadmin/.nanobot-hermes/workspace/packets/<task-id>/
  ↓
Nanobot reviews only the workspace-local packet and writes REPORT.md
  ↓
Hermes copies Nanobot REPORT.md back to project out/reports/<task-id>/
  ↓
Hermes verifies counts/claims against source evidence and writes HERMES_VERIFICATION.md
  ↓
Hermes decides next action; no live vault changes without a separate approval manifest
```

Do not widen Nanobot filesystem permissions just to let it read project paths. If Nanobot reports `outside allowed workspace boundary`, copy a sanitized packet into `/home/hermesadmin/.nanobot-hermes/workspace/packets/` and rerun the same review. Nanobot verdicts are self-reports; Hermes must verify counts and claims before acceptance.

Accepted command shape:

```bash
/home/hermesadmin/.nanobot-hermes/bin/nanobot-headroom-agent <session-id> \
  "Review the proposal-only packet at /home/hermesadmin/.nanobot-hermes/workspace/packets/<task-id>. Use only the packet evidence. Write REPORT.md. Do not mutate live vault, run embeddings, change services/auth/cron, or use paid/direct fallback."
```

This loop is intentionally Nanobot-first and Hermes-second: Nanobot drafts/reviews options; Hermes owns acceptance, source-of-truth verification, user communication, and any future approval manifest.


## Read-only evidence gateway handoff

For recurring Nanobot review, Hermes should expose existing project/server evidence through `http://127.0.0.1:18791/` instead of copying every packet into `~/.nanobot-hermes/workspace`. Nanobot may read gateway URLs under `/reports/`, `/proposals/`, `/queue/`, `/spec-kit/`, and selected server-safe roots such as `/server-work/`, `/server-user-systemd/`, `/hermes-skills/`, and `/nanobot-workspace/`, then produce proposal-only analysis. The gateway is read-only and blocks hidden/secret-like/sensitive paths. Hermes must verify the result against source-of-truth JSON/Markdown and must not treat Nanobot output as authorization for live vault mutation.

If the gateway is unavailable, fall back to the older sanitized workspace-local packet copy.
