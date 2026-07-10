# Quickstart: Validate the Instruction Tree and Tool Registry

## Purpose

Prove that a clean Linux checkout can locate the active Spec Kit feature,
validate the documentation contract, and run project verification without the
live vault or network.

## Prerequisites

- repository checkout on the server;
- Python environment already used by the project;
- Bash and Git;
- no Hermes service restart and no live vault access.

## 1. Resolve the active feature

```bash
cd /home/hermesadmin/work/obsidian-operating-layer
.specify/scripts/bash/check-prerequisites.sh --json
```

Expected: JSON identifies
`specs/001-instruction-tree-tool-documentation` and available feature artifacts.

## 2. Run focused tests

```bash
. .venv/bin/activate
python3 -m pytest tests/test_project_docs_lag_audit.py -q
python3 -m pytest \
  tests/test_project_docs_lag_audit.py::test_instruction_artifacts_do_not_contain_secret_shapes \
  -q
```

Expected after implementation: all focused tests pass.
The secret-shape test emits only repository-relative filenames if it fails.

## 3. Run the real repository audit

```bash
python3 tools/obsidian_project_docs_lag_audit.py \
  --repo . \
  --out-dir out/reports/project-docs-lag-audit/instruction-tree
```

Expected after implementation:

- JSON `status` is `ok`;
- all 58 tracked tool files are represented once;
- required registry fields and controlled values are valid;
- required test, instruction, spec, and canonical links exist;
- no live vault or network operation occurs.

## 4. Run repository verification

```bash
git diff --check
make verify
```

Expected: whitespace check is silent; pytest, Ruff, and compileall pass.

## 5. Review change scope

```bash
git status --short
git diff --stat
```

Expected: only `.specify/`, `specs/`, instruction/documentation files, the
existing docs-lag validator, its CLI description, and its tests are changed.

## 6. Review agent documentation duty

Read `docs/agents/HERMES.md`, `docs/agents/CODEX.md`, and
`docs/agents/NANOBOT.md`. Expected after implementation:

- every role states how it records documentation impact;
- Nanobot covers repository, instructions, tools, tests, runtime evidence,
  plans, and documentation drift;
- Nanobot produces findings or proposals only;
- no command resumes a scheduler job.

## Stop Conditions

Stop and ask the project owner before any command that:

- modifies the live vault;
- installs or enables a Hermes provider;
- changes services, cron jobs, authentication, networking, or packages;
- reads or publishes secrets, private URLs, or personal note bodies;
- commits, pushes, opens a pull request, or deploys without the approval
  required by root instructions.
