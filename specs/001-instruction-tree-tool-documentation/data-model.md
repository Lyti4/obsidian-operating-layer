# Data Model: Instruction Tree and Tool Documentation

## InstructionScope

Represents one directory boundary governed by an `AGENTS.md` file.

| Field | Type | Rules |
|---|---|---|
| `path` | repository-relative path | unique; directory must exist |
| `instruction` | repository-relative Markdown path | file must exist inside `path` |
| `parent_scope` | path or `external` | exactly one parent except external root |
| `purpose` | short text | must describe scope, not repeat all rules |
| `inherits_safety` | boolean | always `true` for repository scopes |
| `canonical_links` | list of paths | every target must exist |

**Relationship:** Scopes form one tree. A child may narrow rules but may not
weaken parent safety, permission, or data boundaries.

## WorkingDocument

Represents a Markdown file that participates in current operation or preserved
project history.

| Field | Type | Rules |
|---|---|---|
| `path` | repository-relative path | file must exist |
| `classification` | enum | `canonical`, `active`, `historical`, or `evidence` |
| `topic_owner` | path | canonical document responsible for current truth |
| `runtime_source` | path or `none` | required for volatile runtime claims |
| `scope` | InstructionScope path | nearest governing scope |
| `notes` | short text | reason for classification or redirect |

**State transitions:** `active` may become `historical`; `evidence` remains
dated evidence; `historical` and `evidence` never become authority without an
explicit new decision.

## ToolRecord

Represents exactly one tracked `tools/*.py` file.

| Field | Type | Rules |
|---|---|---|
| `tool` | path | unique; must exist under `tools/` and end in `.py` |
| `purpose` | short text | non-empty, one responsibility |
| `kind` | enum | `cli` or `internal` |
| `family` | enum | one of eight family identifiers |
| `mode` | enum | `read-only`, `proposal-only`, `sandbox`, or `approved-write` |
| `write_surface` | text/path | `none` or explicit bounded target |
| `inputs` | short text | no secret values |
| `outputs` | short text | no secret values |
| `test` | path/coverage reference | existing test or `covered-by:<path>` for internal code |
| `instruction` | path | existing family guide or runbook |
| `spec` | path or `none` | existing detailed spec when present |
| `status` | enum | `active`, `experimental`, `deprecated`, or `internal` |
| `line_number` | positive integer | parser diagnostic only |

**Validation:** The set of `tool` values must equal the set of tracked
`tools/*.py` paths from the Git index, with no duplicate rows. An isolated
non-Git fixture may derive the set from present tool files.

## ToolFamily

Represents the primary shared guidance for related tools.

| Field | Type | Rules |
|---|---|---|
| `id` | enum | one of eight approved identifiers |
| `guide` | path | one existing file under `docs/tools/families/` |
| `purpose` | short text | non-empty |
| `primary_role` | agent or owner | one primary operating role |
| `data_boundary` | short text | explicit read/write limits |
| `modes` | set | subset of approved ToolRecord modes |
| `members` | set of tool paths | derived from registry, not duplicated by hand |
| `runbooks` | set of paths | all targets must exist |

## AgentContract

Represents one current role contract.

| Field | Type | Rules |
|---|---|---|
| `role` | enum | `Hermes`, `Codex`, or `Nanobot` |
| `purpose` | text | required |
| `allowed_actions` | list | required |
| `forbidden_actions` | list | required |
| `inputs` | list | required |
| `outputs` | list | required |
| `write_boundary` | text | required and consistent with root rules |
| `handoff` | text | required |
| `evidence` | list | required |
| `documentation_duty` | text | update affected docs or record no-impact reason |
| `monitoring_scope` | list | required for Nanobot; seven approved observation areas |
| `runtime_source` | path | must point to `docs/RUNTIME_STATUS.md` |

## DocumentationFinding

Represents one machine-readable mismatch.

| Field | Type | Rules |
|---|---|---|
| `check_name` | stable identifier | non-empty |
| `document` | repository-relative path | expected owner document |
| `status` | enum | `ok`, `lagging`, or `missing-document` |
| `items` | list of strings | exact missing, stale, duplicate, invalid, or broken values |
| `message` | text | actionable and free of note bodies or secrets |

Findings expose repository-relative paths and field names only. Secret-shaped
matched text is never stored in the entity.

**State transition:** A finding moves from `lagging` to `ok` only when the
repository contract is satisfied and the check is rerun.

## FeatureArtifact

Represents one Spec Kit artifact for the active feature.

| Field | Type | Rules |
|---|---|---|
| `path` | repository-relative path | must exist when required by phase |
| `kind` | enum | specification, plan, research, data model, contract, quickstart, checklist, or tasks |
| `feature_directory` | path | must match `.specify/feature.json` |
| `status` | enum | draft, approved, active, complete, or historical |
| `source_links` | list of paths | all targets must exist |

## Relationship Summary

```text
InstructionScope 1 ── * WorkingDocument
InstructionScope 1 ── * AgentContract
ToolFamily       1 ── * ToolRecord
WorkingDocument 1 ── * canonical or runtime references
DocumentationFinding * ── 1 owning document
FeatureArtifact  * ── 1 active feature directory
```

No entity contains live vault note bodies, tokens, private URLs, or runtime
credentials.
