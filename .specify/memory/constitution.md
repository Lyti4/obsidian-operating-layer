# Obsidian Operating Layer Constitution

## Core Principles

### I. Repository Truth Before Assumptions

Current repository files, command output, tests, logs, and explicit user
instructions outrank memory, old handoffs, historical specifications, and
inferred state. Before changing anything, identify the repository root, active
branch, dirty files, applicable `AGENTS.md`, runtime boundaries, and the
smallest verifiable slice.

### II. Read-Only and Proposal-Only by Default

Observation, indexing, search, analysis, and proposal generation are the
default operating modes. Live vault mutation is permitted only through the
documented approved-write path with explicit scope, approval manifest, backup,
verification, and rollback. A model escalation never grants a permission
escalation.

### III. Evidence Before Completion

No change is complete without current evidence. Implementation changes follow
test-first discipline where practical: reproduce or add a failing test, make
the smallest change, run the narrow test, then run broader verification.
Failures and skipped checks are reported directly; stale evidence is not
relabelled as current success.

### IV. Least Privilege and Data Safety

Secrets, tokens, private URLs, subscription links, personal note bodies, and
identifying data must not enter Git, reports, fixtures, or logs. Tests use
temporary or copied data, never the live vault. Paths remain inside approved
roots, generated artifacts stay under ignored output directories, and external
or production actions require a separate confirmation gate.

### V. One Instruction Tree and Complete Tool Coverage

The nearest applicable `AGENTS.md` may narrow but never weaken higher-level
safety rules. Canonical, active, historical, and evidence documents are
explicitly distinguished. Every tracked `tools/*.py` file must have exactly one
registry entry with purpose, kind, family, mode, write surface, inputs, outputs,
test evidence, instruction link, detailed-spec link, and status. Documentation
changes accompany tool-contract changes in the same slice.

Every code, tool, workflow, runtime, or instruction change must identify its
documentation impact. Affected canonical or active documents are updated in the
same slice; when no document changes are needed, the implementation evidence
must state why.

### VI. Small Reversible Slices

Prefer the fewest files, standard-library solutions, existing project patterns,
and reversible changes. Architecture, security, shared contracts, multi-file
migrations, or live runtime work require a Spec Kit feature with explicit
acceptance criteria and rollback. Do not combine repository preparation with
service installation or live configuration changes.

## Project Safety Boundaries

- The live Obsidian vault is not a test fixture.
- Hermes services, providers, cron jobs, authentication, networking, and server
  packages are outside a repo-only slice unless separately approved.
- External tools may read, search, analyze, render, or propose within their
  documented contract; direct vault writes remain forbidden unless routed
  through approved apply.
- Commits, pushes, pull requests, deployments, and externally visible actions
  follow the repository approval rules in the root `AGENTS.md`.
- User-facing explanations are Russian-first. Commands, paths, API names, and
  stable identifiers remain exact; a technical term receives a short Russian
  explanation on first use.

## Development Workflow and Quality Gates

1. Orient from the current repository and instruction tree.
2. Write or update the feature specification and resolve material ambiguity.
3. Produce the implementation plan, requirement-quality checklist, and
   dependency-ordered tasks.
4. Run cross-artifact consistency analysis before implementation.
5. Implement one independently testable slice at a time.
6. Run narrow tests, documentation/link checks, `git diff --check`, and the
   applicable full verification command.
7. Review scope, secrets, generated artifacts, rollback, and untested risks.
8. Record documentation impact and update affected canonical or active files.
9. Commit or publish only with the approval required by root instructions.

## Governance

This constitution governs `.specify/` features and must agree with the root
`AGENTS.md`; system, developer, and explicit user instructions remain higher
authority. Amendments require a documented rationale, affected-artifact review,
migration notes, and a version change. A conflicting feature plan fails its
constitution gate until the conflict is resolved or explicitly approved by the
project owner.

**Version**: 1.0.0 | **Ratified**: 2026-07-10 | **Last Amended**: 2026-07-10
