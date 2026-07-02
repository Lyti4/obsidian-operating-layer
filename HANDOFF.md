# HANDOFF — Obsidian Operating Layer

Date: 2026-06-29
Working directory: `/home/hermesadmin/work/obsidian-operating-layer`

## Start here in a new session

1. Read `AGENTS.md`.
2. Read `docs/spec-kit/21-next-actions-skill-budget.md`.
3. Run:

```bash
git status --short
git diff --name-only
git diff --check
```

4. Do not load broad skills. Use the project skill budget only.
5. Do not touch the live Obsidian vault. Indexing work must stay in sandbox/out paths.

## Current project status

- Safety fixes for indexing wrapper/probe are implemented but not committed.
- Codex full repository review was completed read-only; found issues were fixed.
- Subagent safety audit found no blocking safety issue before real indexing.
- Targeted indexing safety tests were green in the current workstream.
- `ollama serve` is expected to be running locally; model `bge-m3` is available.
- Small sandbox real-candidate probe is green: 1 file indexed, 0 failed, timeout 240s.
- Previous 5-file sandbox probe result: 3 indexed, 2 failed; failures still need diagnosis.
- Full sandbox/full vault-sized run previously hit MCP timeout risk, so do medium sandbox first.

## Skill budget

Default: no skill for simple status checks.

Allowed skills for this project phase:

1. `low-token-codebase-inspection` — quick repo/status/file checks only.
2. `codex` — explicit Codex review/implementation only.
3. `subagent-delegation-triggers` — only for 1-2 focused read-only audit subagents.
4. `requesting-code-review` — pre-commit / acceptance gate only.

Do not load other skills unless Dmitry explicitly asks or the project-local skill budget is updated first.

## Changed files to expect

At last handoff, `git status --short` showed:

```text
 M docs/spec-kit/20-indexing-runtime-acceptance.md
 M src/obslayer/indexing_wrapper.py
 M tests/fixtures/fake_jsonline_mcp_server.py
 M tests/test_indexing_runtime_cli.py
 M tests/test_indexing_stdio_probe.py
 M tests/test_indexing_wrapper.py
 M tools/obsidian_indexing_runtime.py
 M tools/obsidian_indexing_stdio_probe.py
?? docs/spec-kit/21-next-actions-skill-budget.md
```

This handoff file itself may appear as:

```text
?? HANDOFF.md
```

## Verification command to run first

```bash
python3 -m pytest \
  tests/test_indexing_wrapper.py \
  tests/test_indexing_stdio_probe.py \
  tests/test_indexing_runtime_cli.py \
  -q

git diff --check
```

Expected from previous run: targeted pytest green, around 75 tests passed, and `git diff --check` clean.

## Next actions

### 1. Snapshot and verify

- Run git status/diff check.
- Run targeted pytest command above.
- If failures appear, fix before any probe.

### 2. Diagnose previous small failure

- Use only sandbox vault files.
- Prefer a tiny 3-5 file probe, or a 10-small-file medium probe if tiny is already stable.
- Capture sanitized transcript only.
- Verify no raw live vault paths, sandbox absolute paths, derived absolute paths, or secrets leak.

### 3. Medium sandbox probe

Goal: run indexing on 10 small markdown files with increased timeout, not on the live vault.

Report to Dmitry immediately in this format:

```text
Сделано: ...
Проверка: ...
Осталось: ...
Риск/блокер: ...
Следующий шаг: ...
```

### 4. Final Codex GO/NO-GO

After local tests and medium probe are green, run Codex read-only review only.

Suggested brief:

```text
Read-only final GO/NO-GO review for current uncommitted indexing changes.
Focus only on: live vault mutation boundaries, sandbox-only writes, env/secret/path leaks, docs truthfulness, and whether full sandbox indexing may start.
Do not edit files. Return GO or NO-GO with blockers only.
```

### 5. Full sandbox indexing

Only after Codex GO:

- run full indexing against sandbox vault only;
- verify search works;
- verify sanitized report has no raw sensitive paths/secrets;
- verify live vault fingerprint did not change.

### 6. Acceptance and commit

After full sandbox run is green:

- rerun targeted pytest;
- run `git diff --check`;
- write short acceptance note;
- commit only clean, verified changes.

## Known blockers / risks

- MCP timeout on larger runs can recur.
- Two files from previous 5-file probe failed and need explanation.
- Codex↔MCP host-level issue may show `user cancelled MCP tool call`; direct MCP/CLI path works.
- Do not attempt live-vault writes.

## Important safety rules

- Live Obsidian vault is read-only for this workflow.
- Non-dry-run indexing is allowed only against repo-local sandbox/derived roots and only with explicit guard flags.
- Sanitized reports may contain `<SANDBOX_VAULT>` and `<DERIVED_ROOT>`, never raw absolute vault/cache paths.
- Do not print secrets, env tokens, cookies, private keys, or auth files.
