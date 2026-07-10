# Evidence: Agent Contracts and Working Markdown

**Date:** 2026-07-10

**Branch:** `codex/instruction-tree-docs`

**Scope:** T027–T038. Repository role contracts and working Markdown only; no
live vault, provider, service, scheduler, auth, network, or secret change.

## RED evidence

The two new Linux-server tests failed against the previous role files:

```bash
.venv/bin/python -m pytest \
  tests/test_project_docs_lag_audit.py::test_agent_contracts_include_documentation_duty_and_runtime_source \
  tests/test_project_docs_lag_audit.py::test_nanobot_contract_is_project_wide_readonly_observer \
  -q
```

The first failure named `HERMES` because required shared sections were absent.
The second reported that Nanobot did not contain all seven observation area IDs.

## GREEN evidence

After the three role contracts were updated, both tests passed. After T031–T037
working-document alignment, the complete focused file reported nine passing
tests, Ruff reported `All checks passed!`, and `git diff --check` was silent.

## Кто

- Hermes: orchestration, acceptance, safe handoff and evidence checks.
- Codex: bounded repository implementation/review with diff and tests.
- Nanobot: project-wide read-only/proposal-only observer across seven areas.

## Зачем

Prevent permission transfer between agents, stop volatile runtime copies from
becoming authority, and require every change to state `documentation impact`.

## Границы

- Role contracts link `docs/RUNTIME_STATUS.md`; they contain no current job IDs.
- Nanobot role does not activate or resume scheduler jobs.
- Historical boards/specs/snapshots are labelled and point to current sources.
- Live or publication actions still require their governing approval/runbook.

## Проверка

Focused role/docs tests reported nine passing tests and Ruff passed. The first
full suite found two stale compatibility markers in working docs; both were
restored in the new safe context, and `tests/test_p3_polish.py` then reported two
passing tests. A fresh full `make verify` completed in 60 seconds: pytest passed
with one pre-existing skip, Ruff reported `All checks passed!`, and compileall
completed successfully.

Manual sample handoff review:

- Hermes repo-change sample routes bounded implementation to Codex, requires
  independent diff/tests, and returns updated docs or `documentation impact:
  none`; live action routes to the human owner and its runbook.
- Codex implementation sample returns changed files, focused/full checks,
  residual risks and `documentation impact` to Hermes; publication remains
  behind current owner approval.
- Nanobot `documentation-drift` sample returns area, finding, evidence paths,
  risk, recommended action, explicit `handoff target` and `documentation impact`;
  output remains read-only/proposal-only and does not activate scheduler jobs.

## Independent review fixes

Independent read-only review found three actionable documentation issues:

1. Backfill report creation was mistakenly listed under actions allowed without
   extra approval, despite its `approved-write` registry mode.
2. Two copied placeholders were left under the wrong report-template sections.
3. GitHub rollout prose still presented drift-prone multi-repository account
   state as applied/current outside the historical table label.

The policy now requires explicit approval for every approved-write invocation
and forbids running one without its rollback-bearing runbook. The placeholders
were removed, the whole GitHub account/repository snapshot is historical, and
release readiness now distinguishes backed-up existing-note edits from atomic,
non-overwriting new-report creation with delete-only rollback.

After these review fixes, the focused role/docs suite reported 11 passing tests
and Ruff passed. A fresh full `make verify` then completed in 59.3 seconds:
pytest passed with one pre-existing skip, Ruff reported `All checks passed!`,
and compileall completed successfully.

## Следующий шаг

Repeat focused/full verification, then publish this repository-only slice as
its own commit.

## Термины

- `runtime source`: проверяемый источник текущего состояния сервисов/jobs.
- `handoff`: передача ограниченной задачи или решения другой роли.
- `documentation impact`: какие canonical/active документы изменены или почему
  обновление не требуется.
