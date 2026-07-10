# Tasks: Instruction Tree and Tool Documentation

**Input**: Design documents from
`specs/001-instruction-tree-tool-documentation/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`,
`contracts/tool-registry.md`, `quickstart.md`, and
`checklists/requirements.md`

**Tests**: Required. Documentation structure and registry behavior use
test-first changes in `tests/test_project_docs_lag_audit.py`.

**Documentation-impact rule**: Every task closes with either the exact documents
changed or `none — verification only`. This rule applies to all agents and all
handoffs.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: May run in parallel because it changes distinct files and has no
  incomplete dependency.
- **[US#]**: Maps the task to a user story in `spec.md`.
- Every task names exact repository paths.

## Phase 1: Setup and Artifact Integrity

**Purpose**: Confirm the approved planning foundation before implementation.

- [x] T001 Run `.specify/scripts/bash/check-prerequisites.sh --json` and confirm it resolves `specs/001-instruction-tree-tool-documentation/` with no global Spec Kit dependency. [Docs: none — verification only]
- [x] T002 Scan `.specify/memory/constitution.md` and `specs/001-instruction-tree-tool-documentation/*.md` for unresolved template tokens, invalid line endings, and missing required artifacts. [Docs: affected planning artifact if drift is found; otherwise none — verification only]

---

## Phase 2: Foundational Test Fixture

**Purpose**: Prepare one isolated fixture used by every structural user story.

**Critical**: No production documentation validator change begins before this
fixture remains green against the existing marker checks.

- [x] T003 Extend `_write_minimal_docs()` in `tests/test_project_docs_lag_audit.py` with a temporary `tools/example.py`, minimal instruction-tree files, and a valid `docs/tools/INDEX.md` row without changing existing assertions. [Docs: none — test fixture only]
- [x] T004 Run `python3 -m pytest tests/test_project_docs_lag_audit.py -q` and record the pre-feature passing baseline in `specs/001-instruction-tree-tool-documentation/evidence/mvp-instruction-tree-2026-07-10.md`. [Docs: the evidence file]

**Checkpoint**: Existing audit behavior is preserved and the fixture can host
new structural tests.

---

## Phase 3: User Story 1 — Find the Governing Instruction (Priority: P1) MVP

**Goal**: A reader can derive the applicable instruction chain from any sampled
project area.

**Independent Test**: Required instruction files exist, root links resolve, and
the documented scope chain covers root, docs, roles, tools, safety core, and
tests without weakening root safety.

- [x] T005 [US1] Add `test_instruction_tree_required_files_and_root_links()` and `test_instruction_navigation_is_at_most_three_links()` to `tests/test_project_docs_lag_audit.py`, run them, and record the expected missing-file RED result in `specs/001-instruction-tree-tool-documentation/evidence/mvp-instruction-tree-2026-07-10.md`. [Docs: the evidence file]
- [x] T006 [P] [US1] Create `docs/AGENTS.md` with classification, authority-link, Russian terminology, and same-slice documentation-impact rules. [Docs: `docs/AGENTS.md`]
- [x] T007 [P] [US1] Create `docs/agents/AGENTS.md` with the shared role-contract schema and prohibition on weakening root permissions. [Docs: `docs/agents/AGENTS.md`]
- [x] T008 [P] [US1] Create `tools/AGENTS.md` with CLI/internal boundaries, safe defaults, registry/test obligations, and same-slice documentation updates. [Docs: `tools/AGENTS.md`]
- [x] T009 [P] [US1] Create `src/obslayer/AGENTS.md` with path containment, approved-write, dry-run, and trust-boundary rules. [Docs: `src/obslayer/AGENTS.md`]
- [x] T010 [P] [US1] Create `tests/AGENTS.md` with temporary-fixture, no-live-vault, negative-permission, and evidence rules. [Docs: `tests/AGENTS.md`]
- [x] T011 [US1] Create `docs/INSTRUCTION_TREE.md` with the complete precedence tree, canonical owners, active-document inventory, directory classifications, conflict rule, and documentation-impact contract. [Docs: `docs/INSTRUCTION_TREE.md`]
- [x] T012 [US1] Refactor `AGENTS.md` to link `.specify/`, `docs/INSTRUCTION_TREE.md`, `docs/tools/INDEX.md`, nested scopes, agent contracts, and `docs/RUNTIME_STATUS.md` while preserving all root safety and approval gates. [Docs: `AGENTS.md`]
- [x] T013 [P] [US1] Add the human entry path to `README.md` and link security authority from `SECURITY.md` without copying volatile runtime claims. [Docs: `README.md`, `SECURITY.md`]
- [x] T014 [US1] Run `python3 -m pytest tests/test_project_docs_lag_audit.py -q`, make the US1 instruction-tree tests GREEN without live-system dependencies, and append the focused/full verification results to `specs/001-instruction-tree-tool-documentation/evidence/mvp-instruction-tree-2026-07-10.md`. [Docs: the evidence file]

**Checkpoint**: User Story 1 is independently navigable and safe.

---

## Phase 4: User Story 2 — Understand Every Tool (Priority: P1)

**Goal**: Every tracked tool-layer file is documented exactly once and belongs
to one primary family.

**Independent Test**: The registry set equals the 58-file baseline, required
cells are non-empty, both internal modules are classified, and all family-guide
paths exist.

- [x] T015 [US2] Add `test_tool_registry_covers_tracked_tools_exactly_once()`, `test_tool_set_uses_git_index_with_fixture_fallback()`, and `test_internal_support_modules_are_not_cli()` to `tests/test_project_docs_lag_audit.py`, then confirm RED against the absent registry parser. [Docs: none — failing tests only]
- [x] T016 [US2] Add the minimal frozen `ToolRegistryEntry`, Git-index resolver, and `parse_tool_registry()` to `src/obslayer/project_docs_lag_audit.py` so registry coverage can pass independently before the full US4 validator. [Docs: `specs/001-instruction-tree-tool-documentation/contracts/tool-registry.md`]
- [x] T017 [US2] Populate `docs/tools/INDEX.md` with the exact 12-column contract and one evidence-backed row for each of the 58 tracked `tools/*.py` files, replacing its truthful migration coverage state. [Docs: `docs/tools/INDEX.md`]
- [x] T018 [P] [US2] Create `docs/tools/families/hermes-memory.md` covering `tools/hermes_obslayer_memory.py`, read-only context limits, timeout/fail-open behavior, privacy, tests, and future provider boundary. [Docs: `docs/tools/families/hermes-memory.md`]
- [x] T019 [P] [US2] Create `docs/tools/families/core-vault-workflow.md` covering observe, propose, sandbox, approved apply, verify, and controlled-autonomy tools with write gates and runbooks. [Docs: `docs/tools/families/core-vault-workflow.md`]
- [x] T020 [P] [US2] Create `docs/tools/families/indexing-graphify-semantic.md` covering indexing, Graphify, embedding, semantic manifest/query/proposal, and derived-data boundaries. [Docs: `docs/tools/families/indexing-graphify-semantic.md`]
- [x] T021 [P] [US2] Create `docs/tools/families/link-hygiene.md` covering target discovery, triage, scoring, selection, suppression, and safe-link policy tools. [Docs: `docs/tools/families/link-hygiene.md`]
- [x] T022 [P] [US2] Create `docs/tools/families/operator-control-plane.md` covering review queues, decision ledger, readiness, dashboard, and unified control-plane indexes. [Docs: `docs/tools/families/operator-control-plane.md`]
- [x] T023 [P] [US2] Create `docs/tools/families/agent-collaboration.md` covering Hermes/Codex handoff and Nanobot evidence/review packet tools without permission transfer. [Docs: `docs/tools/families/agent-collaboration.md`]
- [x] T024 [P] [US2] Create `docs/tools/families/reports-evidence.md` covering audits, doctors, reports, acceptance bundles, benchmarks, and sanitized evidence outputs. [Docs: `docs/tools/families/reports-evidence.md`]
- [x] T025 [P] [US2] Create `docs/tools/families/internal-support.md` for `tools/_bootstrap.py` and `tools/common.py`, including indirect test coverage and non-CLI status. [Docs: `docs/tools/families/internal-support.md`]
- [x] T026 [US2] Compare every registry row against source, `--help`, tests, and current docs; for any `approved-write` tool without a rollback-bearing guide create a file under `docs/runbooks/` named from its Python filename stem, then run focused coverage tests and confirm 58 unique paths, two `internal` records, and zero missing runbooks. [Docs: `docs/tools/INDEX.md`, affected family guides, and any deterministic missing runbook]

**Checkpoint**: User Story 2 provides complete tool discovery even before the
full drift validator is implemented.

---

## Phase 5: User Story 3 — Work Within an Agent Contract (Priority: P2)

**Goal**: Hermes, Codex, and Nanobot operate under consistent boundaries;
Nanobot observes the whole project and every agent records documentation impact.

**Independent Test**: The three contracts contain every required section,
Nanobot names seven observation areas and proposal-only outputs, and runtime
state is linked rather than copied.

- [x] T027 [US3] Add `test_agent_contracts_include_documentation_duty_and_runtime_source()` and `test_nanobot_contract_is_project_wide_readonly_observer()` to `tests/test_project_docs_lag_audit.py`, then confirm RED against current role files. [Docs: none — failing tests only]
- [x] T028 [P] [US3] Update `docs/agents/HERMES.md` with orchestration boundary, documentation-impact duty, runtime-source link, and explicit handoff for repository or live actions. [Docs: `docs/agents/HERMES.md`]
- [x] T029 [P] [US3] Update `docs/agents/CODEX.md` with repository-change, test evidence, documentation-impact, commit/push approval, and live-system handoff rules. [Docs: `docs/agents/CODEX.md`]
- [x] T030 [P] [US3] Update `docs/agents/NANOBOT.md` with seven project-wide observation areas, read-only/proposal-only outputs, alert/handoff format, documentation-drift duty, and no scheduler activation. [Docs: `docs/agents/NANOBOT.md`]
- [x] T031 [US3] Replace `HANDOFF.md` with a short current pointer and mark `ROLE_NOTES.md` historical with links to `docs/agents/` and `docs/RUNTIME_STATUS.md`. [Docs: `HANDOFF.md`, `ROLE_NOTES.md`]
- [x] T032 [P] [US3] Align authority and current-state links in `docs/PROJECT_OVERVIEW.md`, `docs/PROJECT_MAP.md`, `docs/ARCHITECTURE.md`, and `docs/DECISIONS.md`. [Docs: the four named files]
- [x] T033 [P] [US3] Align tool and skill ownership in `docs/TOOLS_POLICY.md`, `docs/PROJECT_SKILLS.md`, and `docs/component-inventory.md`. [Docs: the three named files]
- [x] T034 [P] [US3] Classify and align operating instructions in `docs/operator-guide.md`, `docs/controlled-autonomy.md`, `docs/release-readiness.md`, `docs/orchestration-board.md`, `docs/github-integration.md`, `docs/github-integration-rollout.md`, and `docs/github-marketplace-integrations.md`. [Docs: the seven named files]
- [x] T035 [P] [US3] Align skill guidance in `docs/skills/README.md`, `docs/skills/codex.md`, `docs/skills/graphify.md`, `docs/skills/nanobot.md`, `docs/skills/obsidian-layer-triage-kanban.md`, and `docs/skills/obsidian.md`. [Docs: the six named files]
- [x] T036 [P] [US3] Align risk, rollback, and authority links in `docs/runbooks/approved-live-apply.md`, `docs/runbooks/observe-propose-verify.md`, `docs/runbooks/proposal-review.md`, and `docs/runbooks/sandbox-indexing.md`. [Docs: the four named files]
- [x] T037 [US3] Correct stale command/runtime authority in `docs/spec-kit/30-orchestrator-operating-spec.md`, `docs/RUNTIME_STATUS.md`, `docs/report-template.md`, and `docs/telegram-summary-templates.md` without rewriting dated evidence. [Docs: the four named files]
- [x] T038 [US3] Run focused role-contract tests and manually review one sample change handoff from each agent for an explicit documentation-impact result. [Docs: none — verification only]

**Checkpoint**: User Story 3 is independently usable; Nanobot is a standing
observer contract but no job is resumed.

---

## Phase 6: User Story 4 — Detect Documentation Drift (Priority: P2)

**Goal**: The existing docs-lag audit detects registry and instruction-tree
drift with actionable findings.

**Independent Test**: A complete temporary repository passes; missing, stale,
duplicate, empty, invalid, malformed, broken-link, and undocumented-tool
mutations each fail with the specified check name.

- [ ] T039 [US4] Add parameterized RED tests for all ten structural check names plus `test_instruction_artifacts_do_not_contain_secret_shapes()` in `tests/test_project_docs_lag_audit.py`; the secret test must report filenames only. [Docs: none — failing tests only]
- [ ] T040 [US4] Extend the existing `ToolRegistryEntry` and `parse_tool_registry()` in `src/obslayer/project_docs_lag_audit.py` with controlled values, line-number diagnostics, malformed-row handling, and filenames-only secret-shape support without an external dependency. [Docs: contract already updated; no additional documentation impact]
- [ ] T041 [US4] Add `tool_registry_checks()` to `src/obslayer/project_docs_lag_audit.py` for exact set equality, uniqueness, required fields, controlled values, cross-field rules, and repository-link existence. [Docs: `specs/001-instruction-tree-tool-documentation/contracts/tool-registry.md` if behavior changes]
- [ ] T042 [US4] Add `instruction_link_checks()` and integrate structural checks into `run_project_docs_lag_audit()` while preserving `ProjectDocsLagAudit.to_dict()` and existing CLI exit semantics. [Docs: `docs/INSTRUCTION_TREE.md` if canonical link contract changes]
- [ ] T043 [US4] Review `DEFAULT_CHECKS` in `src/obslayer/project_docs_lag_audit.py`; preserve still-current marker checks and replace obsolete 15-minute/runtime phrase checks with structural current-source requirements. [Docs: `AGENTS.md`, `docs/RUNTIME_STATUS.md`, and `docs/INSTRUCTION_TREE.md` only if the governing requirement changes]
- [ ] T044 [US4] Update the CLI description and report boundary in `tools/obsidian_project_docs_lag_audit.py` and `src/obslayer/project_docs_lag_audit.py` to state repository structural validation rather than marker-only validation. [Docs: `docs/tools/INDEX.md`, `docs/tools/families/reports-evidence.md`]
- [ ] T045 [US4] Run `python3 -m pytest tests/test_project_docs_lag_audit.py -q` twice and confirm identical green results. [Docs: none — verification only]
- [ ] T046 [US4] Run `python3 tools/obsidian_project_docs_lag_audit.py --repo . --out-dir out/reports/project-docs-lag-audit/instruction-tree` and resolve every real-repository finding without copying obsolete text into current policy. [Docs: affected canonical or active file named by each finding]

**Checkpoint**: User Story 4 protects all earlier stories against drift.

---

## Phase 7: User Story 5 — Plan Future Work Consistently (Priority: P3)

**Goal**: A clean Linux checkout can use the repository-local planning system
and distinguish new active features from legacy project records.

**Independent Test**: Project-local scripts resolve the active feature and its
available artifacts without a global CLI or network.

- [ ] T047 [US5] Add `.specify/`, `specs/`, active-feature precedence, and legacy `docs/spec-kit/` status to `docs/INSTRUCTION_TREE.md`, `README.md`, and `AGENTS.md`. [Docs: the three named files]
- [ ] T048 [US5] Run `.specify/scripts/bash/check-prerequisites.sh --json`, `.specify/scripts/bash/setup-plan.sh --json`, and `.specify/scripts/bash/setup-tasks.sh --json`; confirm all paths remain inside `specs/001-instruction-tree-tool-documentation/`. [Docs: none — verification only]
- [ ] T049 [US5] Execute every safe command in `specs/001-instruction-tree-tool-documentation/quickstart.md` through the focused test step and correct any inaccurate expected result. [Docs: `specs/001-instruction-tree-tool-documentation/quickstart.md` if correction is required]

**Checkpoint**: User Story 5 is reproducible offline on the target server.

---

## Phase 8: Polish, Evidence, and Independent Review

**Purpose**: Prove cross-story consistency and leave a reusable owner report.

- [ ] T050 Run a requirement-to-task traceability review across `spec.md`, `plan.md`, `checklists/requirements.md`, and `tasks.md`; add any missing task before implementation completion. [Docs: affected feature artifact]
- [ ] T051 Run `python3 -m pytest tests/test_project_docs_lag_audit.py::test_instruction_artifacts_do_not_contain_secret_shapes -q`, then run template-token, terminology, link, and `git diff --check` scans across `.specify/`, `specs/`, `AGENTS.md`, `docs/`, `tools/AGENTS.md`, `src/obslayer/AGENTS.md`, and `tests/AGENTS.md`. [Docs: affected file if a finding is corrected; otherwise none — verification only]
- [ ] T052 Run `make verify` and record pytest, Ruff, and compileall evidence without treating skipped or failed checks as success. [Docs: none — verification only]
- [ ] T053 Perform an independent review of instruction precedence, 58-row coverage, approved-write/runbook mapping, Nanobot boundaries, secrets, generated artifacts, and live-system exclusions. [Docs: affected file if review finds an issue; otherwise none — review only]
- [ ] T054 Create `docs/audits/instruction-tree-tool-documentation-2026-07-10.md` with Кто, Зачем, Почему, Что делаем, Границы, Проверка, Следующий шаг, and Термины, including exact verification evidence and unresolved risks. [Docs: the audit file]
- [ ] T055 Review `git status --short`, `git diff --stat`, and explicit diffs; confirm no vault, Hermes config, service, cron, auth, network, secret, or tracked `out/` change is included, and record that rollback is repository-only with no live-system rollback. [Docs: none — verification only]

---

## Dependencies and Execution Order

### Phase Dependencies

- Phase 1 has no dependency.
- Phase 2 depends on Phase 1 and blocks structural test work.
- US1 and US2 both depend on Phase 2 and may proceed independently after the
  shared fixture is stable.
- US3 depends on US1's role-scope contract and may overlap with US2 family-guide
  writing in different files.
- US4 depends on the US1 instruction tree and US2 registry contract.
- US5 depends on the planning foundation and US1 authority links, not on US4.
- Phase 8 depends on all selected user stories.

### User Story Dependencies

- **US1 (P1):** No other story dependency after Phase 2; recommended MVP.
- **US2 (P1):** No other story dependency after Phase 2; required before US4.
- **US3 (P2):** Depends on US1's shared role schema.
- **US4 (P2):** Depends on US1 and US2 artifacts.
- **US5 (P3):** Depends on Phase 1 and final US1 authority links.

### Parallel Opportunities

- T006–T010 use distinct instruction files.
- T017–T024 create distinct family guides.
- T028–T030 update distinct agent contracts.
- T032–T036 update disjoint documentation groups.
- US1 and US2 may run in parallel after Phase 2, but registry rows should not be
  split across writers because `docs/tools/INDEX.md` is one source of truth.

## Parallel Example: User Story 2

After T016 creates the registry contract and member list, family guides may be
written in parallel:

```text
T017: docs/tools/families/hermes-memory.md
T018: docs/tools/families/core-vault-workflow.md
T019: docs/tools/families/indexing-graphify-semantic.md
T020: docs/tools/families/link-hygiene.md
T021: docs/tools/families/operator-control-plane.md
T022: docs/tools/families/agent-collaboration.md
T023: docs/tools/families/reports-evidence.md
T024: docs/tools/families/internal-support.md
```

## Implementation Strategy

### MVP First

1. Complete setup and the shared fixture.
2. Implement US1 only.
3. Stop and verify instruction discovery independently.
4. Add US2 registry coverage.
5. Add role refresh, structural drift protection, and planning reproducibility.

### Checkpoints

- After every user story, run its focused test and inspect the exact diff.
- Do not begin live provider, voice, scheduler, or vault integration in this
  feature.
- Do not commit, push, open a pull request, or resume Nanobot jobs without the
  approval required by root instructions.

## Task Summary

- Total tasks: 55
- Setup and foundation: 4
- US1: 10
- US2: 12
- US3: 12
- US4: 8
- US5: 3
- Polish and evidence: 6
- Suggested MVP: Phases 1–3, User Story 1 only
