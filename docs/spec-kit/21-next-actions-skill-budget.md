# 21 — Next Actions Skill Budget

Date: 2026-06-29
Project: Obsidian Operating Layer
Mode: lean continuation plan; avoid loading broad skills unless explicitly needed.

## Goal

Reach a safe start of real Obsidian indexing through the project wrapper, without exposing live vault paths/secrets and without allowing live-vault mutation.

## Current state

- Codex review and subagent safety audit found no current blocking safety issue after the fixes.
- Targeted tests for indexing safety are green.
- Ollama + `bge-m3` are available.
- A 1-file sandbox real-candidate indexing probe is green.
- A previous 5-file sandbox probe had 3 indexed and 2 failed; this still needs diagnosis before full indexing.
- Full indexing previously hit MCP timeout risk, so the next step is medium-sized sandbox validation, not live/full vault indexing.

## Skill budget

Default: load no skill for simple status checks.

Use only these skills when needed:

1. `low-token-codebase-inspection`
   - Use for quick repo/file/status checks in Telegram.
   - Purpose: keep context small and avoid broad reading.

2. `codex`
   - Use only for explicit Codex review or implementation.
   - Preferred for final GO/NO-GO review after local tests pass.

3. `subagent-delegation-triggers`
   - Use only when launching parallel subagents.
   - For this project: max 1-2 subagents, read-only audit briefs only, no broad research.

4. `requesting-code-review`
   - Use only before commit or acceptance gate.
   - Purpose: focused pre-commit safety/quality review.

Usually avoid for this phase:

- `project-spec-kit-triage-kanban` — too heavy unless rebuilding the whole project workflow.
- `graphify` — not needed unless asking architecture/codebase relationship questions.
- `system-design` — not needed for current stabilization.
- `clean-code`, `simplify-code`, `systematic-debugging` — only if a concrete bug/refactor appears.
- creative/research/productivity/devops skills unrelated to indexing.

## Next actions

### Step 1 — Snapshot state

Commands:

```bash
git status --short
git diff --name-only
git diff --check
```

GO if:
- only expected files are modified;
- `git diff --check` is clean.

STOP if:
- unexpected files changed;
- generated artifacts are staged/modified outside `out/` or ignored locations.

### Step 2 — Run focused safety tests

Command:

```bash
python3 -m pytest \
  tests/test_indexing_wrapper.py \
  tests/test_indexing_stdio_probe.py \
  tests/test_indexing_runtime_cli.py \
  -q
```

GO if all tests pass.

STOP if any safety, redaction, or non-dry-run guard test fails.

### Step 3 — Diagnose the 5-file sandbox failure

Run a small sandbox probe with 3-5 files and collect sanitized output only.

GO if:
- failures are understood;
- no live vault paths appear in stdout/stderr/reports;
- sandbox paths are redacted as `<SANDBOX_VAULT>`;
- derived paths are redacted as `<DERIVED_ROOT>`.

STOP if:
- live vault path leaks;
- secret/env data leaks;
- MCP writes outside repo-local sandbox/derived roots;
- failure reason is unknown after one focused retry.

### Step 4 — Medium sandbox probe

Run medium-sized sandbox indexing with increased timeout.

GO if:
- indexing completes without timeout;
- search over indexed notes returns expected results;
- sanitized transcript passes path/secret checks;
- live vault fingerprint is unchanged.

STOP if:
- timeout repeats;
- failed files are unexplained;
- fingerprint check detects live vault mutation.

### Step 5 — Final Codex GO/NO-GO

Use Codex only after local tests and medium probe pass.

Brief:

```text
Read-only final GO/NO-GO review for current uncommitted indexing changes.
Focus only on: live vault mutation boundaries, sandbox-only writes, env/secret/path leaks, docs truthfulness, and whether full sandbox indexing may start.
Do not edit files. Return GO or NO-GO with blockers only.
```

GO if Codex returns no blocking issues.

STOP if Codex reports medium/high safety blockers.

### Step 6 — Full sandbox indexing

Start full indexing only against sandbox vault, not live vault.

GO if:
- full sandbox run completes;
- sanitized report has no raw live/sandbox/derived absolute path leaks;
- search works;
- live vault fingerprint remains unchanged.

STOP if:
- timeout remains unresolved;
- any raw sensitive path/secret appears;
- any live vault mutation is detected.

### Step 7 — Acceptance report and commit

After full sandbox indexing is green:

```bash
git diff --check
python3 -m pytest tests/test_indexing_wrapper.py tests/test_indexing_stdio_probe.py tests/test_indexing_runtime_cli.py -q
```

Then write a short acceptance note with:
- commands run;
- reports produced;
- files changed;
- GO/NO-GO result;
- remaining known limitations.

Commit only after the acceptance note and tests are clean.

## Minimal reporting format for Dmitry

Use this compact update format:

```text
Сделано: ...
Проверка: ...
Осталось: ...
Риск/блокер: ...
Следующий шаг: ...
```

## Work discipline

- No broad skill loading.
- No Kanban/card movement unless explicitly requested.
- No subagents for simple status.
- No live vault write.
- No full indexing before green medium sandbox probe and final Codex GO.
