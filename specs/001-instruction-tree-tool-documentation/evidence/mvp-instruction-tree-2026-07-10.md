# Evidence: Instruction Tree MVP

**Date:** 2026-07-10

**Branch:** `codex/instruction-tree-docs`

**Scope:** T001–T014 only. Repository planning and instruction files; no live
vault, Hermes config, service, cron, auth, network, or secret change.

## Baseline before implementation

Command:

```bash
. .venv/bin/activate
make verify
```

Result:

- pytest completed successfully with one pre-existing skip;
- Ruff: `All checks passed!`;
- compileall completed successfully.

## RED evidence

Command:

```bash
python3 -m pytest \
  tests/test_project_docs_lag_audit.py::test_project_docs_lag_audit_ok \
  tests/test_project_docs_lag_audit.py::test_instruction_tree_required_files_and_root_links \
  tests/test_project_docs_lag_audit.py::test_instruction_navigation_is_at_most_three_links \
  -q
```

Observed result before instruction files were created: one existing audit test
passed and both new tests failed. The first failure reported seven missing
instruction files. The second failed because `docs/INSTRUCTION_TREE.md` did not
exist. No unrelated failure was used as RED evidence.

## GREEN evidence

Focused commands:

```bash
python3 -m pytest tests/test_project_docs_lag_audit.py -q
python3 -m ruff check tests/test_project_docs_lag_audit.py
git diff --check
```

Result: four tests passed, Ruff passed, and `git diff --check` was silent.

Full command:

```bash
make verify
```

Result:

- full pytest suite passed with one pre-existing skip;
- Ruff: `All checks passed!`;
- compileall completed successfully.

## Independent review

The first review found three issues before publication:

1. root commit/push/PR approval was not explicit;
2. navigation testing trusted declared counts instead of computing transitions;
3. baseline and RED evidence were not stored in the repository.

All three were corrected before commit.

## Post-review verification

After the three review fixes, the focused suite again reported four passing
tests, Ruff passed, and `git diff --check` was silent. A fresh full
`make verify` then completed successfully: the full pytest suite passed with one
pre-existing skip, Ruff reported `All checks passed!`, and compileall completed
successfully.

## Documentation impact

Updated root authority, README/security entrypoints, nested instruction scopes,
the instruction map, the truthful migration registry, tests, Spec Kit planning
artifacts, and this evidence record.
