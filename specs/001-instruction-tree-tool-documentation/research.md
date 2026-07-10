# Research: Instruction Tree and Tool Documentation

## Decision 1: Use project-local Spec Kit 0.12.0

**Decision:** Track the official bundled `.specify/` infrastructure with Bash
scripts and Codex integration metadata.

**Rationale:** The server has no global `specify` command, while project-local
templates and scripts make future planning reproducible and offline.

**Alternatives considered:** Continue only with numbered `docs/spec-kit/`
files; install a global server CLI; copy another project's `.specify/`. These
were rejected because they lack active-feature automation, expand server state,
or risk importing unrelated project policy.

## Decision 2: One Markdown tool registry

**Decision:** Make `docs/tools/INDEX.md` the human and machine source of truth.

**Rationale:** A second JSON or YAML registry would create synchronization work.
The required values contain no table delimiters and can be validated with a
small standard-library parser.

**Alternatives considered:** One file per tool; Markdown generated from JSON;
unstructured prose search. These increase file count, create duplicate truth,
or cannot guarantee completeness.

## Decision 3: Extend the existing docs-lag audit

**Decision:** Add structural checks to
`src/obslayer/project_docs_lag_audit.py` while preserving its output model and
CLI exit behavior.

**Rationale:** The project already exposes the tool through the Makefile and has
focused tests. Reuse avoids another command and another report format.

**Alternatives considered:** New validator command; shell-only link checker;
external Markdown linter. They duplicate responsibility, provide weak semantic
checks, or add a dependency.

## Decision 4: Eight primary families

**Decision:** Assign each tool to one primary family and express secondary
relationships through links.

**Rationale:** A single owner guide prevents contradictory instructions while
still allowing cross-family discovery.

**Alternatives considered:** Multiple family membership; 58 individual guides;
no family layer. These create duplicate authority or make navigation difficult.

## Decision 5: Preserve history, centralize current state

**Decision:** Keep dated audits and old plans unchanged, classify them as
historical or evidence, and point volatile runtime claims to
`docs/RUNTIME_STATUS.md`.

**Rationale:** Rewriting old evidence destroys chronology, while copying current
runtime facts into many files creates drift.

**Alternatives considered:** Rewrite every historical document; delete stale
files; tolerate competing current claims. Each loses evidence or keeps
ambiguity.

## Decision 6: Isolated validation only

**Decision:** Test registry and instruction checks in temporary repositories and
run the real audit only against tracked repository files.

**Rationale:** Documentation correctness does not require live vault, service,
network, credentials, or personal note content.

**Alternatives considered:** Validate against the live vault or Hermes runtime.
Rejected because it expands risk without improving the documentation contract.

## Resolved Unknowns

- Spec Kit version: 0.12.0, confirmed by generated metadata.
- Server script type: Bash.
- Baseline tool count: 58 tracked `tools/*.py` files.
- Internal modules: `tools/_bootstrap.py` and `tools/common.py`.
- Registry source: Markdown only.
- Structural validator: existing project docs lag audit.
- Live-system dependency: none.

## Decision 7: Nanobot is a bounded project-wide observer

**Decision:** Define Nanobot's standing role across repository structure,
instructions, tool coverage, tests, current runtime evidence, active plans, and
documentation drift. Its outputs are findings, review packets, or proposals.

**Rationale:** The owner wants one lightweight role continuously watching the
whole project, while the existing safety model prohibits implicit writes or
permission expansion.

**Alternatives considered:** Limit Nanobot to one subsystem; allow automatic
fixes; resume all existing scheduled jobs as part of documentation work. The
first misses cross-area drift, and the latter two expand runtime authority
outside this repo-only feature.

## Decision 8: Git index defines the real tool set

**Decision:** Use `git ls-files -- tools/*.py` in a real checkout and a
filesystem fallback only in isolated non-Git test fixtures.

**Rationale:** “Tracked tool” must mean the Git index, not an accidental local
or generated Python file. The fallback keeps unit fixtures small without
weakening real-repository validation.

**Alternatives considered:** Always scan the filesystem; require every fixture
to initialize Git; hard-code 58 names. These respectively include untracked
noise, add unnecessary fixture setup, or become stale after the next tool.

## Decision 9: Built-in filenames-only secret-shape test

**Decision:** Add a standard-library test for common private-key and provider
token shapes. A failure reports only the repository-relative filename.

**Rationale:** No supported `gitleaks`, `detect-secrets`, or `git-secrets`
command is installed on the server, and printing matched lines could expose the
value being protected.

**Alternatives considered:** Add a dependency; print matching diff lines; omit
the explicit scan. These increase setup, risk disclosure, or fail SC-008.
