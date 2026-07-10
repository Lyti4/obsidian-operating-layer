# Feature Specification: Instruction Tree and Tool Documentation

**Feature Directory**: `001-instruction-tree-tool-documentation`

**Created**: 2026-07-10

**Status**: Approved for planning

**Input**: The project owner wants a clear hierarchy of instructions from
global rules to narrow tool and agent guidance, complete documentation for every
repository tool, refreshed working Markdown instructions, and a durable Spec
Kit workflow for future development.

**Design Source**: `docs/spec-kit/52-instruction-tree-and-tool-documentation.md`

## User Scenarios & Testing

### User Story 1 - Find the Governing Instruction (Priority: P1)

As the project owner or an agent, I can start from any project area and identify
which instruction is authoritative, which narrower rules apply, and where to
find the current operating state.

**Why this priority**: Incorrect instruction precedence can cause unsafe writes,
stale decisions, or work in the wrong subsystem. The hierarchy is the foundation
for every later documentation improvement.

**Independent Test**: Select representative files in the repository root,
`docs/`, `docs/agents/`, `tools/`, `src/obslayer/`, and `tests/`; for each file,
a reader can identify the applicable instruction chain and safety boundary
without relying on chat history.

**Acceptance Scenarios**:

1. **Given** a reader starts at the repository root, **When** they follow the
   instruction map, **Then** they can distinguish project-wide rules from
   documentation, role, tool, safety-core, and test rules.
2. **Given** a narrow instruction conflicts with a higher safety rule, **When**
   the precedence policy is applied, **Then** the higher safety rule wins and
   the unresolved conflict is surfaced.
3. **Given** a document contains a runtime claim, **When** the reader needs its
   current status, **Then** the document directs them to the canonical runtime
   source rather than presenting an undated copy as current truth.

---

### User Story 2 - Understand Every Tool (Priority: P1)

As the project owner or a future agent, I can look up every tracked Python file
under `tools/` and understand why it exists, whether it is a command or internal
module, what it may write, how it is tested, and which detailed instruction
governs it.

**Why this priority**: The repository currently contains 58 tool-layer files.
Incomplete coverage makes safe reuse, retirement, and extension unreliable.

**Independent Test**: Compare the tracked `tools/*.py` set with the registry;
all 58 baseline files appear exactly once, each row has every required field,
and both internal support modules are clearly separated from commands.

**Acceptance Scenarios**:

1. **Given** the baseline repository contains 58 tracked tool files, **When**
   the registry is compared with Git, **Then** coverage is exactly 58 of 58 with
   no stale or duplicate rows.
2. **Given** a reader selects any registry row, **When** they follow its links,
   **Then** they reach an existing test or explicit coverage statement and an
   existing family instruction.
3. **Given** a new tool file is added without documentation, **When** the
   documentation quality gate runs, **Then** it reports a failure identifying
   the missing file.

---

### User Story 3 - Work Within an Agent Contract (Priority: P2)

As Hermes, Codex, or Nanobot, I receive a role contract that states my purpose,
allowed and forbidden actions, inputs, outputs, write boundary, handoff rules,
required evidence, and documentation duty without duplicating volatile runtime
facts. Nanobot can observe the whole project and surface cross-area drift while
remaining read-only/proposal-only.

**Why this priority**: Role clarity reduces accidental permission expansion and
prevents one agent's notes from silently becoming another agent's authority.

**Independent Test**: Review the three role contracts against the shared role
template; each contains all required sections, inherits root safety rules, and
links current runtime state rather than copying it.

**Acceptance Scenarios**:

1. **Given** an agent receives a task outside its allowed actions, **When** it
   applies its contract, **Then** it stops or hands the task to the appropriate
   role without claiming wider permission.
2. **Given** a runtime service or schedule changes, **When** a role contract is
   read, **Then** it remains valid because volatile status is referenced from
   the canonical runtime document.
3. **Given** code, a tool, a workflow, runtime state, or an instruction changes,
   **When** an agent completes the slice, **Then** it updates affected canonical
   or active documents or records why no documentation change is required.
4. **Given** Nanobot observes any project area, **When** it detects drift, risk,
   or missing evidence, **Then** it produces a bounded finding or proposal and
   does not apply the change itself.

---

### User Story 4 - Detect Documentation Drift (Priority: P2)

As a maintainer, I receive an automatic failure when tools, registry fields,
instruction links, or active document classifications drift apart.

**Why this priority**: A written hierarchy is useful only while changes that
break it are detected before publication.

**Independent Test**: In an isolated test repository, remove a registry row,
break a linked file, omit a required field, add an undocumented tool, and insert
an invalid controlled value; each mutation produces a specific failing finding,
while the complete fixture passes.

**Acceptance Scenarios**:

1. **Given** the repository and registry agree, **When** the quality gate runs,
   **Then** it reports an `ok` result.
2. **Given** one structural contract is broken, **When** the gate runs, **Then**
   it reports `lagging` and names the broken contract without reading the live
   vault.
3. **Given** an old phrase-based rule no longer represents current policy,
   **When** the gate is revised, **Then** the obsolete phrase is removed or
   replaced by a structural requirement instead of being copied into current
   instructions.

---

### User Story 5 - Plan Future Work Consistently (Priority: P3)

As the project owner or an implementation agent, I can create future features
from a project-local specification, plan, checklist, and tasks workflow without
reconstructing templates from another repository.

**Why this priority**: The instruction migration is the immediate need; the
planning framework makes future memory, voice, semantic indexing, and Agentic
OS work repeatable after this slice.

**Independent Test**: From a clean checkout, a reader can locate the project
constitution and templates, resolve the active feature, and run the documented
prerequisite and planning setup commands without network access.

**Acceptance Scenarios**:

1. **Given** the repository is freshly cloned on the Linux server, **When** the
   project-local setup scripts are invoked, **Then** they locate the active
   feature and create or report the expected planning artifacts.
2. **Given** an older project document exists under `docs/spec-kit/`, **When** a
   new active feature is planned, **Then** the old document remains preserved as
   history and does not override the active feature under `specs/`.

### Edge Cases

- A tracked tool is renamed, deleted, or appears twice in the registry.
- An internal support module is incorrectly documented as a user command.
- A tool has no direct test but is covered through callers.
- A tool belongs conceptually to several families.
- A registry row contains an empty field, an invalid controlled value, or a
  link to a missing file.
- A historical document contains a command or runtime claim that is no longer
  current.
- A narrow `AGENTS.md` attempts to weaken a root safety boundary.
- A generated Spec Kit template still contains unresolved sample placeholders.
- The documentation check runs in a temporary repository without the live vault,
  network, Hermes service, or user secrets.

## Requirements

### Functional Requirements

- **FR-001**: The project MUST define one documented precedence chain from
  external instructions through the root instruction to the nearest narrow
  instruction.
- **FR-002**: The project MUST provide scoped instruction files for
  documentation, role contracts, tool development, the safety core, and tests.
- **FR-003**: Narrow instructions MUST NOT weaken root safety, permission, data,
  or publication boundaries.
- **FR-004**: The project MUST maintain a human-readable instruction map that
  identifies every canonical instruction owner and scope.
- **FR-005**: Working documents MUST be classified as `canonical`, `active`,
  `historical`, or `evidence`.
- **FR-006**: Current runtime facts MUST have one canonical source, and other
  working documents MUST link to it instead of copying volatile state as truth.
- **FR-007**: Every tracked `tools/*.py` file MUST appear exactly once in the
  tool registry.
- **FR-008**: Every tool row MUST include its exact path, purpose, kind, family,
  safety mode, write surface, inputs, outputs, test evidence, instruction link,
  detailed-spec link, and lifecycle status.
- **FR-009**: Tool kinds MUST distinguish executable commands from internal
  support modules.
- **FR-010**: Tools MUST be assigned to exactly one primary family, with
  cross-family relationships expressed as links rather than duplicate rows.
- **FR-011**: The registry MUST cover the eight approved families: Hermes
  memory; core vault workflow; indexing, Graphify, and semantic search; link
  hygiene; operator and control plane; agent collaboration; reports and
  evidence; and internal support modules.
- **FR-012**: A family guide MUST define purpose, role ownership, data boundary,
  safety modes, shared flow, member tools, checks, runbooks, limitations, and
  Russian explanations of first-use technical terms.
- **FR-013**: A separate runbook MUST exist for operations that write to the
  vault, change approved state, affect services or schedules, cross agent
  boundaries, or require backup and rollback.
- **FR-014**: Hermes, Codex, and Nanobot contracts MUST share one required
  structure and MUST state allowed actions, forbidden actions, write boundary,
  handoff, and evidence.
- **FR-015**: Historical handoffs, role notes, audits, and old plans MUST remain
  available but MUST NOT present themselves as current authority.
- **FR-016**: The documentation quality gate MUST compare the tracked tool set
  with registry rows and report missing, stale, or duplicate entries.
- **FR-017**: The quality gate MUST validate required fields, controlled values,
  and referenced repository paths without contacting the live vault or network.
- **FR-018**: The quality gate MUST fail when a new tool lacks documentation or
  when a canonical instruction link is broken.
- **FR-019**: Obsolete phrase-only checks MUST be reviewed and replaced with
  structural checks when the phrase is no longer a governing requirement.
- **FR-020**: The project MUST include a local Spec Kit constitution, templates,
  Linux-compatible scripts, active-feature pointer, and feature artifacts.
- **FR-021**: Existing `docs/spec-kit/` documents MUST remain available as
  historical project material while new active features use `specs/`.
- **FR-022**: User-facing summaries MUST be Russian-first; exact commands,
  paths, API names, and stable identifiers MUST remain unchanged.
- **FR-023**: A technical term MUST receive a short Russian explanation on its
  first user-facing use and need not be repeatedly translated.
- **FR-024**: This repository slice MUST NOT change the live vault, Hermes
  providers, services, schedules, authentication, networking, or secrets.
- **FR-025**: Commit, push, pull request, deployment, and other external actions
  MUST remain behind the approvals required by the root project instructions.
- **FR-026**: Every agent contract MUST require a documentation-impact decision
  for code, tool, workflow, runtime, or instruction changes and same-slice
  updates for affected canonical or active documents.
- **FR-027**: Nanobot MUST be defined as the project-wide observer for
  repository structure, instructions, tool coverage, tests, current runtime
  evidence, open plans, and documentation drift while remaining
  read-only/proposal-only.
- **FR-028**: Nanobot monitoring instructions MUST distinguish the standing
  role contract from current scheduler state; enabling or resuming scheduled
  jobs MUST require a separate runtime approval.
- **FR-029**: In a Git checkout, the authoritative tool set MUST come from the
  Git index; an isolated non-Git test fixture MAY use its present `tools/*.py`
  files as an explicit fallback.
- **FR-030**: Documentation findings and secret-shape checks MUST report only
  repository paths, field names, and check identifiers, never matched secret
  values, private URLs, note bodies, or credentials.
- **FR-031**: An `approved-write` tool without an existing rollback-bearing
  runbook MUST block completion until a deterministic tool-named runbook is
  created and linked.
- **FR-032**: Repository rollback requirements MUST be distinct from operational
  rollback; this repo-only feature MUST require no live-system rollback.
- **FR-033**: Adding a new instruction scope MUST require updating the human
  instruction map and its structural link validation in the same slice.
- **FR-034**: The instruction map MUST explicitly inventory every `canonical`
  and `active` working instruction and define directory-level classification
  rules for `historical` and `evidence` material.

### Key Entities

- **Instruction Scope**: A directory boundary, its governing instruction file,
  its parent scope, and the safety rules it inherits.
- **Working Document**: A Markdown document with a classification, topic owner,
  current source link, and lifecycle status.
- **Tool Record**: One tracked tool-layer file and its documentation, safety,
  evidence, and lifecycle fields.
- **Tool Family**: The single primary operating guide shared by related tool
  records.
- **Agent Contract**: The role-specific permissions, prohibitions, handoffs, and
  evidence obligations for Hermes, Codex, or Nanobot.
- **Documentation Finding**: A specific mismatch between repository state and a
  documentation contract.
- **Feature Artifact**: A linked specification, plan, research note, data model,
  contract, quickstart, checklist, or task list for one active feature.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All 58 baseline tool files are documented exactly once, with zero
  missing, stale, or duplicate registry entries.
- **SC-002**: One hundred percent of registry rows contain all required fields
  and resolve every required repository link.
- **SC-003**: All three agent contracts satisfy the shared contract structure
  and contain zero permission conflicts with root rules.
- **SC-004**: A reader can reach the governing instruction, current runtime
  source, and tool guidance for any sampled project area in no more than three
  documentation links.
- **SC-005**: Each defined structural drift scenario produces a named failing
  finding, while the complete isolated fixture produces an `ok` result.
- **SC-006**: All active working Markdown instructions are classified and have
  zero unresolved conflicts or broken canonical links.
- **SC-007**: Project-local planning prerequisites and artifact resolution work
  from a fresh Linux checkout without network access.
- **SC-008**: Repository verification completes with zero new test, lint,
  compile, whitespace, secret-scan, or tracked-generated-artifact failures.
- **SC-009**: The completed slice changes zero live vault notes, provider
  settings, services, scheduled jobs, authentication values, or network rules.
- **SC-010**: One hundred percent of implementation tasks and final handoffs
  state the documentation impact and identify updated documents or a reasoned
  no-impact result.
- **SC-011**: The Nanobot contract covers all seven approved observation areas
  and every sample finding remains read-only/proposal-only with an explicit
  handoff target.

## Assumptions

- The baseline for registry coverage is the 58 tracked `tools/*.py` files on
  commit `2c9e4323049832b266f5cb1b3a79eb844b538874`.
- Baseline success criterion SC-001 proves the initial 58-row migration; after
  that migration, FR-007 and FR-029 require dynamic equality with the current
  Git index rather than a permanent hard-coded count.
- The approved hierarchy is option A from the design discussion and
  `docs/spec-kit/52-instruction-tree-and-tool-documentation.md`.
- Existing tests and source code provide enough evidence to classify tool
  purpose and coverage; unknown claims are omitted rather than invented.
- One registry plus eight family guides is preferable to 58 separate tool
  documents unless a tool needs its own risk-specific runbook.
- `docs/RUNTIME_STATUS.md` remains the canonical source for volatile runtime
  state.
- Spec Kit version 0.12.0 with Bash scripts is the project-local planning
  baseline for the Linux server.
- Repository-only implementation may proceed without live Hermes or vault
  access; runtime integration remains a separate approved slice.
- Existing Nanobot scheduler definitions may remain paused; this feature
  defines the standing observer contract but does not resume jobs.
