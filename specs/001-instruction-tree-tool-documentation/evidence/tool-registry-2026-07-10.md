# Evidence: Tool Registry Foundation

**Date:** 2026-07-10

**Branch:** `codex/instruction-tree-docs`

**Scope:** T015–T026. Registry parser/resolver, 58 tool records, eight family
guides, approved-write runbooks, reviewer fixes, tests, and evidence; no live
vault, Hermes config, service, cron, auth, network, or secret change.

## Environment correction

The first command used system `python3` and stopped because that interpreter did
not contain `pytest`. This was an environment error, not RED evidence. All
evidence below uses the repository interpreter at `.venv/bin/python`.

## RED evidence

Command:

```bash
.venv/bin/python -m pytest tests/test_project_docs_lag_audit.py -q
```

Observed before implementation: test collection failed because
`parse_tool_registry` did not exist in
`src/obslayer/project_docs_lag_audit.py`. This is the intended missing behavior
for T015.

## Focused GREEN evidence

Commands:

```bash
.venv/bin/python -m pytest \
  tests/test_project_docs_lag_audit.py::test_tool_set_uses_git_index_with_fixture_fallback \
  -q
.venv/bin/python -m ruff check \
  src/obslayer/project_docs_lag_audit.py \
  tests/test_project_docs_lag_audit.py
```

Result: the resolver test passed and Ruff reported `All checks passed!`.

## Remaining RED boundary

Command:

```bash
.venv/bin/python -m pytest \
  tests/test_project_docs_lag_audit.py::test_tool_registry_covers_tracked_tools_exactly_once \
  tests/test_project_docs_lag_audit.py::test_internal_support_modules_are_not_cli \
  -q
```

Result: both tests failed as expected. The Git-index resolver found exactly 58
tracked Python tools, while the migration registry still contained zero tool
records. The two internal support rows were therefore also absent. This is the
honest starting state for T017, not a completed registry claim.

## Registry and family-guide evidence

After T017–T025 were implemented, the focused server command reported three
passing tests:

```bash
.venv/bin/python -m pytest \
  tests/test_project_docs_lag_audit.py::test_tool_registry_covers_tracked_tools_exactly_once \
  tests/test_project_docs_lag_audit.py::test_tool_set_uses_git_index_with_fixture_fallback \
  tests/test_project_docs_lag_audit.py::test_internal_support_modules_are_not_cli \
  -q
```

The authoritative Git-index set and the registry both contained 58 unique
paths. A separate read-only loop invoked `--help` for all 56 `kind=cli` tools
with `PYTHONDONTWRITEBYTECODE=1`; all returned successfully.

Local structural checks confirmed:

- eight family guides and all eight approved family IDs;
- every registry instruction, test, and non-`none` specification path exists;
- every tool is named by its linked family guide or runbook;
- all four `approved-write` rows link to rollback-bearing runbooks;
- no table row contains an extra Markdown pipe;
- no secret-shaped value was found in the new guides or runbooks.

After the owner explicitly confirmed that the SSH server is trusted and under
their control, the initially required backfill/swap runbooks were synchronized
to the branch. Independent review later added the fourth approved-write row and
the tool-named `docs/runbooks/hermes_codex_run.md`.

## User Story 2 completion evidence

Additional checks reported:

- `approved_write_runbooks=4`; every linked runbook exists and contains
  rollback or restoration instructions;
- `secret_shape_scan=clean`; the scan reported filenames only on failure;
- `git diff --check` completed silently;
- the full `make verify` completed successfully in 63.5 seconds: pytest passed
  with one pre-existing skip, Ruff reported `All checks passed!`, and compileall
  completed successfully.

No live vault, provider, service, scheduler, authentication, network, or secret
state was read or changed by this repository slice.

## Independent review fixes

The first independent review found two actionable safety/documentation issues:

1. `hermes_codex_run.py` was incorrectly classified as `sandbox` even though
   implementation mode can change the canonical repository.
2. `obsidian_backfill_report.py` allowed `--out` to escape `--reports-dir` and
   silently overwrite an existing report.

The runner is now `approved-write` and links the rollback-bearing
`docs/runbooks/hermes_codex_run.md`. Backfill now resolves and contains the
output path under `--reports-dir`, refuses existing outputs, returns code 2 for
both violations, and has two RED/GREEN regression tests. The focused reviewer
fix suite reported 26 passing tests and Ruff reported `All checks passed!`.

The re-review then found that a separate `exists()` check still left a race
window before `write_text()`. The final local fix uses exclusive `open("x")`,
which atomically refuses an output created by another process. It also corrected
this evidence file from the early T015–T016/three-runbook wording to the complete
T015–T026/four-runbook scope. After synchronization, the 26-test focused suite
passed, Ruff passed, and a fresh full `make verify` completed in 63.5 seconds
with one pre-existing skip and no failures.

## Documentation impact

Updated the feature task state and added this evidence record. The registry
contract itself was already defined in
`specs/001-instruction-tree-tool-documentation/contracts/tool-registry.md`.
