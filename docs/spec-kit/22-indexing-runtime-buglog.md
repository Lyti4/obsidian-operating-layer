# 22 — Indexing Runtime Buglog

Date: 2026-06-29
Project: Obsidian Operating Layer
Scope: sandbox/derived indexing only; no live vault mutation.

## Purpose

Track indexing runtime failures found during sandbox acceptance so they are not lost between runs and can be fixed systematically.

## Open bugs

### BUG-001 — Full sandbox indexing times out in monolithic `index_vault`

- Status: open
- Severity: blocking for full sandbox acceptance
- Symptom: `Timed out waiting for MCP response to tools/call` during full sandbox run.
- Evidence:
  - run: `full-sandbox-acceptance-20260629-rerun-cleanup-node24-190304`
  - process exit: `2`
  - partial DB: `/home/hermesadmin/work/obsidian-operating-layer/out/external-indexing-spike/full-sandbox-acceptance-20260629-rerun-cleanup-node24-190304/data/semantic.sqlite`
  - partial counters observed: `notes=49`, `chunks=642`
  - aborted files included:
    - `Memory-Vault/00 Memory Graph Index.md`
    - `Memory-Vault/Hermes/Blonde Hair Care Trends Article - 2026-06-17.md`
    - `Memory-Vault/Hermes/Hermes Scraper Toolkit.md`
- Current hypothesis: one large MCP `index_vault` call has no usable progress/resume boundary and can hang until outer timeout.
- Proposed fix:
  - add batched/resumable indexing through candidate `paths` parameter;
  - add checkpoint after each batch;
  - add per-batch timeout plus overall run budget;
  - mark failed/stalled batches and continue where safe.

### BUG-002 — No raw/sanitized report is produced when timeout aborts the run

- Status: open
- Severity: high for diagnostics
- Symptom: timeout path exits without complete structured raw/sanitized report.
- Evidence: latest full sandbox timeout left a partial DB but no final raw/sanitized report for the failed run.
- Proposed fix:
  - write partial report from `finally`/timeout handler;
  - include start/end timestamps, timeout reason, DB counters, stderr tail, failed/active batch, cleanup status, and sanitized paths.

### BUG-003 — Candidate file-level errors are not captured clearly

- Status: open
- Severity: medium/high
- Symptom: candidate returns failed counts without useful per-file failure reason in sanitized output.
- Evidence:
  - single largest markdown diagnostic sandbox returned `indexed=0`, `failed=1`;
  - file: `Soul-Organism-Graphify-Vault/Repo Reports/tools__hermes-agent_GRAPH_REPORT.md`;
  - size observed: `1,563,937` bytes;
  - no explicit file-level error detail was found in report/npm logs.
- Proposed fix:
  - capture candidate response fields verbatim in raw report;
  - sanitize and preserve per-file error records when present;
  - if candidate does not expose reasons, record batch/file identity and stderr tail.

### BUG-004 — `paths` batch can be rejected by protected paths

- Status: fixed/covered by tests
- Severity: medium
- Symptom: first `paths` batch was rejected because it included a protected `_Archive` path.
- Evidence: candidate reported path denial for a `Soul-Vault/_Archive/...` path during small batch experiment.
- Fix implemented:
  - batched `paths` input is prefiltered through wrapper exclude/protection policy before calling candidate;
  - skipped protected paths are recorded in checkpoint/progress JSON;
  - regression coverage verifies `_Archive`/protected paths are skipped and not sent to MCP.
- Verification:
  - targeted pytest: `81 passed`;
  - real candidate smoke `batched-paths-smoke-20260629-201938`: `status=ok`, `index_vault_failed=0`, two one-file batches completed.

### BUG-005 — Main probe/runtime does not yet expose batched `paths` workflow

- Status: fixed/covered by tests for stdio probe; runtime integration remains follow-up if needed
- Severity: blocking for reliable full sandbox indexing
- Symptom: candidate supports `paths`, but the production probe still relied on monolithic full-vault indexing.
- Fix implemented:
  - added `--paths-file`, `--batch-size`, `--batch-checkpoint`, `--discover-paths`, and `--resume` to stdio probe;
  - checkpoint/progress JSON is written under derived root only;
  - resume validates current request identity and skips only matching completed batches;
  - failed batches are recorded under `failed_batches`, not `completed_batches`, so resume will not silently skip failed paths;
  - `--paths-file` is restricted under derived root to avoid live/secret file reads and error leaks.
- Verification:
  - targeted pytest: `81 passed`;
  - Codex read-only review blocker fixed with regression tests;
  - real candidate smoke `batched-paths-smoke-20260629-201938` produced checkpoint with 2 completed batches and sanitized report with no absolute live/sandbox/derived path leaks.

### BUG-006 — Need to verify actual Node 24 execution path

- Status: open
- Severity: medium
- Symptom: stderr shows npm `EBADENGINE` warning requiring Node `>=24.0.0` while current Node appears as `v22.22.3`.
- Evidence:
  - package: `@dalecb/obsidian-semantic-mcp@0.2.1`
  - required: `node >=24.0.0`
  - warning showed current: `node v22.22.3`, `npm 10.9.8`
- Unknown: whether MCP itself actually runs under Node 24 when invoked through the current wrapper, or whether the warning is emitted by host npm before delegated execution.
- Proposed fix:
  - add a small explicit preflight/log line recording `node --version` for the actual candidate command environment;
  - avoid relying on warning text alone.

## Fixed or mitigated issues

### FIX-001 — Timeout cleanup left possible orphan MCP/Node processes

- Status: fixed/covered by tests
- Symptom: timeout could leave candidate process tree alive.
- Fix implemented:
  - candidate process starts in its own process group;
  - close/timeout cleanup terminates the process group with `SIGTERM`, then `SIGKILL` if needed.
- Verification:
  - targeted tests passed after adding orphan cleanup regression;
  - post-timeout checks found no orphan `obsidian-semantic-mcp`/`node` processes;
  - Ollama model was manually stopped after diagnostics.

## Next implementation order

1. Implement BUG-004 filtering in the real batched path.
2. Implement BUG-005 batched/resumable `paths` workflow.
3. Implement BUG-002 partial report on timeout.
4. Improve BUG-003 per-file/batch error capture.
5. Verify BUG-006 actual Node runtime.
6. Re-run limited batch sandbox, then full sandbox acceptance only if limited run is green.

## Update rule

When a new indexing runtime failure is observed, add an entry here with:

- stable bug id;
- symptom;
- exact sandbox/derived artifact path when safe;
- observed command/result summary;
- current hypothesis;
- proposed fix or next diagnostic step;
- status update when fixed and verified.
