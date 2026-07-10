# Instruction Tree and Tool Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` for independently reviewable
> documentation families or `superpowers:executing-plans` for checkpointed
> inline execution. Steps use checkbox (`- [ ]`) syntax in `tasks.md`.

**Goal:** Build a single, verifiable instruction hierarchy and complete tool
documentation system for the Obsidian Operating Layer repository.

**Architecture:** Keep the root `AGENTS.md` as project-wide authority and add
nearest-scope instruction files for documentation, roles, tools, safety-core
code, and tests. Store every tool in one machine-checked Markdown registry,
group tools into eight family guides, and extend the existing documentation lag
audit to validate coverage, controlled fields, and links without using the live
vault or network.

**Tech Stack:** Markdown, Python 3.11 standard library, pytest, Ruff, Bash,
Git, project-local Spec Kit 0.12.0.

---

## Input Artifacts

- `specs/001-instruction-tree-tool-documentation/spec.md`
- `docs/spec-kit/52-instruction-tree-and-tool-documentation.md`
- `.specify/memory/constitution.md`
- `AGENTS.md`
- `docs/RUNTIME_STATUS.md`
- `docs/TOOLS_POLICY.md`
- `docs/agents/HERMES.md`
- `docs/agents/CODEX.md`
- `docs/agents/NANOBOT.md`
- `src/obslayer/project_docs_lag_audit.py`
- `tests/test_project_docs_lag_audit.py`

## Technical Context

**Language/Version:** Python 3.11 and Markdown.

**Primary Dependencies:** Python standard library only for validation; existing
pytest and Ruff development dependencies.

**Storage:** Tracked repository files. Generated audit output remains under
ignored `out/reports/project-docs-lag-audit/`.

**Testing:** Focused pytest tests using `tmp_path`, then `make verify`.

**Target Platform:** Linux server checkout; planning scripts use Bash.

**Performance Goal:** Complete locally without network access and record elapsed
time as evidence; no brittle hard threshold is imposed on different server
loads.

**Constraints:** No live vault reads or writes, no Hermes provider/config/service
changes, no cron/auth/network changes, no new Python dependency, no secret or
note-body logging.

**Scale:** 58 baseline tool-layer files, 115 tracked Markdown files in the base
commit, three agent contracts, eight tool families, five nested instruction
scopes.

## Constitution Check Before Design

| Gate | Result | Evidence |
|---|---|---|
| Repository truth used | PASS | Baseline counts and current files were read from commit `2c9e432` and the active branch. |
| Read-only/proposal default preserved | PASS | The feature changes repository docs, tests, and a repository-only audit. |
| Evidence required | PASS | Structural checks, focused tests, link checks, and `make verify` are planned. |
| Least privilege/data safety | PASS | Tests use temporary repositories and never access the live vault. |
| Instruction and tool coverage | PASS | The feature explicitly requires nearest-scope instructions and 58-of-58 registry coverage. |
| Small reversible slices | PASS | Work is divided into independently testable user-story phases. |

No gate violation requires an exception.

## Phase 0 Research Decisions

Research is complete in `research.md`. There are no unresolved clarifications.
The main decisions are:

1. Use official project-local Spec Kit 0.12.0 with Bash scripts.
2. Keep one authoritative Markdown registry rather than Markdown plus a second
   JSON source.
3. Extend the existing documentation lag audit instead of creating another
   validator.
4. Preserve historical documents and mark their authority instead of rewriting
   past evidence.
5. Create family guides for all tools and individual runbooks only for risky or
   multi-step operations.

## Phase 1 Design

### Data model

`data-model.md` defines `InstructionScope`, `WorkingDocument`, `ToolRecord`,
`ToolFamily`, `AgentContract`, `DocumentationFinding`, and `FeatureArtifact`.

### Contract

`contracts/tool-registry.md` defines the exact Markdown header, allowed values,
path rules, internal-module test coverage syntax, and structural findings.

### Quickstart

`quickstart.md` defines offline setup, focused tests, the repository audit,
complete verification, expected results, and forbidden live actions.

## File Structure and Responsibilities

### Project-local planning infrastructure

**Created by the official bundled generator:**

- `.specify/init-options.json` — local Spec Kit mode and version.
- `.specify/integration.json` — Codex integration metadata.
- `.specify/integrations/codex.manifest.json` — Codex integration contract.
- `.specify/integrations/speckit.manifest.json` — Spec Kit workflow contract.
- `.specify/memory/constitution.md` — non-negotiable project principles.
- `.specify/scripts/bash/*.sh` — offline Linux planning setup scripts.
- `.specify/templates/*.md` — feature artifact templates.
- `.specify/workflows/*` — workflow registry and definition.
- `.specify/feature.json` — active feature pointer.

**Created for this feature:**

- `specs/001-instruction-tree-tool-documentation/spec.md`
- `specs/001-instruction-tree-tool-documentation/plan.md`
- `specs/001-instruction-tree-tool-documentation/research.md`
- `specs/001-instruction-tree-tool-documentation/data-model.md`
- `specs/001-instruction-tree-tool-documentation/contracts/tool-registry.md`
- `specs/001-instruction-tree-tool-documentation/quickstart.md`
- `specs/001-instruction-tree-tool-documentation/checklists/requirements.md`
- `specs/001-instruction-tree-tool-documentation/tasks.md`

### Instruction hierarchy

**Create:**

- `docs/AGENTS.md` — Markdown lifecycle, status, links, language, and registry
  update rules.
- `docs/INSTRUCTION_TREE.md` — precedence map, canonical owners, active working
  document inventory, and historical/evidence boundaries.
- `docs/agents/AGENTS.md` — required role-contract structure.
- `tools/AGENTS.md` — CLI and internal-module safety/documentation rules.
- `src/obslayer/AGENTS.md` — path, mutation, and trust-boundary rules.
- `tests/AGENTS.md` — isolated evidence and fixture rules.

**Modify:**

- `AGENTS.md` — keep project-wide authority concise and link narrow scopes,
  Spec Kit, runtime truth, and tool registry.
- `README.md` — add the human entry path to the instruction tree and registry.
- `SECURITY.md` — link approved-write and secret-handling authority without
  duplicating runtime state.

### Tool documentation

**Create:**

- `docs/tools/INDEX.md` — exactly 58 baseline rows with all contract fields.
- `docs/tools/families/hermes-memory.md`
- `docs/tools/families/core-vault-workflow.md`
- `docs/tools/families/indexing-graphify-semantic.md`
- `docs/tools/families/link-hygiene.md`
- `docs/tools/families/operator-control-plane.md`
- `docs/tools/families/agent-collaboration.md`
- `docs/tools/families/reports-evidence.md`
- `docs/tools/families/internal-support.md`

Existing `docs/runbooks/*.md` remain operation-specific. New runbooks are not
created unless registry review finds an approved-write or service operation
without an existing rollback-bearing guide.

**Create after verification:**

- `docs/audits/instruction-tree-tool-documentation-2026-07-10.md` — dated
  evidence in the structural blocks Кто, Зачем, Почему, Что делаем, Границы,
  Проверка, Следующий шаг, and Термины.

### Working Markdown instructions

**Review and modify where the instruction map identifies drift:**

- `HANDOFF.md` — short current pointer, not an authority copy.
- `ROLE_NOTES.md` — historical redirect to current role contracts.
- `docs/PROJECT_OVERVIEW.md`
- `docs/PROJECT_MAP.md`
- `docs/ARCHITECTURE.md`
- `docs/DECISIONS.md`
- `docs/TOOLS_POLICY.md`
- `docs/PROJECT_SKILLS.md`
- `docs/RUNTIME_STATUS.md`
- `docs/operator-guide.md`
- `docs/controlled-autonomy.md`
- `docs/release-readiness.md`
- `docs/agents/HERMES.md`
- `docs/agents/CODEX.md`
- `docs/agents/NANOBOT.md`
- `docs/skills/README.md`
- `docs/skills/codex.md`
- `docs/skills/graphify.md`
- `docs/skills/nanobot.md`
- `docs/skills/obsidian-layer-triage-kanban.md`
- `docs/skills/obsidian.md`
- `docs/runbooks/approved-live-apply.md`
- `docs/runbooks/observe-propose-verify.md`
- `docs/runbooks/proposal-review.md`
- `docs/runbooks/sandbox-indexing.md`
- `docs/spec-kit/30-orchestrator-operating-spec.md`

Each file either receives current status/authority links or is explicitly
classified without unnecessary prose rewrites. Historical audits and dated
evidence are not rewritten.

All three agent contracts receive a mandatory documentation-impact section.
Nanobot additionally receives a project-wide observation matrix covering
repository structure, instruction drift, tool coverage, tests, current runtime
evidence, active plans, and documentation consistency. Its outputs are findings
or proposals only; scheduler activation is excluded.

### Structural validator

**Modify:**

- `src/obslayer/project_docs_lag_audit.py` — parse the registry table, compare it
  to tracked tool files, validate controlled values and repository links, and
  report structural findings through the existing audit result.
- `tools/obsidian_project_docs_lag_audit.py` — update CLI help to describe both
  marker and structural checks; preserve output and exit-code contract.
- `tests/test_project_docs_lag_audit.py` — add isolated fixtures for complete,
  missing, stale, duplicate, invalid-field, missing-link, and undocumented-tool
  cases.

No new dependency or second validator module is required.

## Validator Design

Add a frozen `ToolRegistryEntry` dataclass with the 12 registry columns and a
`line_number` field for diagnostics. Define controlled sets:

```python
ALLOWED_TOOL_KINDS = {"cli", "internal"}
ALLOWED_TOOL_FAMILIES = {
    "hermes-memory",
    "core-vault-workflow",
    "indexing-graphify-semantic",
    "link-hygiene",
    "operator-control-plane",
    "agent-collaboration",
    "reports-evidence",
    "internal-support",
}
ALLOWED_TOOL_MODES = {"read-only", "proposal-only", "sandbox", "approved-write"}
ALLOWED_TOOL_STATUSES = {"active", "experimental", "deprecated", "internal"}
```

The existing module exposes three focused helpers with these exact signatures:
`parse_tool_registry(path: Path) -> list[ToolRegistryEntry]`,
`tool_registry_checks(repo: Path, entries: list[ToolRegistryEntry]) ->
list[DocLagCheck]`, and `instruction_link_checks(repo: Path) ->
list[DocLagCheck]`.

Tool discovery uses `git -C <repo> ls-files -- tools/*.py` when Git metadata is
available. Only isolated non-Git test fixtures fall back to present
`tools/*.py` files. Diagnostics return paths, field names, and check IDs only;
matched secret-shaped values are never included.

The parser recognizes exactly this table header:

```text
tool | purpose | kind | family | mode | write_surface | inputs | outputs | test | instruction | spec | status
```

The implementation keeps `ProjectDocsLagAudit.to_dict()` and CLI exit behavior
compatible. Structural checks are appended as ordinary `DocLagCheck` objects so
existing report consumers do not require a schema migration.

## Test-First Sequence

1. Extend the temporary fixture with a minimal valid instruction tree and tool
   registry.
2. Add registry coverage tests and run them against the old code; expected
   result is failure because the registry parser is absent.
3. Implement the minimal registry dataclass, Git-index resolver, and parser so
   User Story 2 can pass independently.
4. Populate all 58 real registry rows and family guides.
5. Add parameterized mutations for missing, stale, duplicate, invalid, empty,
   malformed, broken-link, and secret-shape cases.
6. Extend the minimal parser with the remaining structural checks.
7. Run `python3 -m pytest tests/test_project_docs_lag_audit.py -q` until green.
8. Run the CLI against the real repository and remove or migrate obsolete
   marker failures based on current canonical policy.
9. Run the filenames-only secret-shape test, `git diff --check`, and
   `make verify`.

## Migration Slices

1. **Planning foundation:** `.specify/` and the complete feature artifacts.
2. **Authority MVP:** nested instruction files, instruction tree, and root links.
3. **Tool coverage:** registry and eight family guides with 58-of-58 coverage.
4. **Role and working-doc refresh:** agent contracts, mandatory documentation
   impact, Nanobot project-wide observation, and stale active pointers.
5. **Drift gate:** structural validator, tests, real-repository audit.
6. **Polish and evidence:** full verification, scope review, audit report, and
   owner handoff.

Each slice is reviewable and can be reverted independently before merge.

## Validation Gates

### Narrow

```bash
python3 -m pytest tests/test_project_docs_lag_audit.py -q
python3 -m pytest \
  tests/test_project_docs_lag_audit.py::test_instruction_artifacts_do_not_contain_secret_shapes \
  -q
python3 tools/obsidian_project_docs_lag_audit.py \
  --repo . \
  --out-dir out/reports/project-docs-lag-audit/instruction-tree
git diff --check
```

Expected after implementation: focused tests pass; the real audit reports
`status=ok`; the secret-shape test reports paths only and finds no candidate;
whitespace check is silent.

### Broad

```bash
make verify
```

Expected: pytest, Ruff, and compileall pass with no new failures.

### Manual scope review

```bash
git status --short
git diff --stat
git diff -- . ':!out/'
```

Expected: only repository planning, documentation, validator, and test files are
changed. No vault, config, service, cron, auth, secret, or tracked generated
artifact appears.

Every slice report also names affected canonical/active documents or states why
the slice has no documentation impact.

## Rollback

Before merge, abandon or revert the feature branch. After merge, revert the
explicit repository commit. The feature does not alter live Hermes or Obsidian
state, so no operational rollback is required.

## Constitution Check After Design

All pre-design gates still pass. The design adds no dependency, network call,
live data access, permission expansion, or competing source of tool truth. The
single Markdown registry and existing audit module satisfy the simplicity and
complete-coverage principles.

## Execution Handoff

Implementation starts only after cross-artifact analysis confirms that
`spec.md`, this plan, the requirement checklist, and `tasks.md` agree. Commits,
pushes, pull requests, and live runtime changes remain separate approval gates.
