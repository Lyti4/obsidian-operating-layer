# Contract: Tool Registry and Structural Documentation Audit

## Registry Location

The authoritative registry is `docs/tools/INDEX.md`. It contains explanatory
prose followed by exactly one table with this header and column order:

```text
| tool | purpose | kind | family | mode | write_surface | inputs | outputs | test | instruction | spec | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
```

Each subsequent non-separator row represents one tracked `tools/*.py` file.
Cells may use Markdown code spans but must not contain the pipe character.

## Field Contract

| Field | Allowed form |
|---|---|
| `tool` | unique repository-relative `tools/*.py` path |
| `purpose` | non-empty plain description |
| `kind` | `cli` or `internal` |
| `family` | one approved family ID |
| `mode` | `read-only`, `proposal-only`, `sandbox`, or `approved-write` |
| `write_surface` | `none` or explicit bounded path/state description |
| `inputs` | non-empty, sanitized description |
| `outputs` | non-empty, sanitized description |
| `test` | existing `tests/*.py` path or `covered-by:tests/*.py` |
| `instruction` | existing path under `docs/tools/families/` or `docs/runbooks/` |
| `spec` | existing repository path or `none` |
| `status` | `active`, `experimental`, `deprecated`, or `internal` |

## Approved Families

- `hermes-memory`
- `core-vault-workflow`
- `indexing-graphify-semantic`
- `link-hygiene`
- `operator-control-plane`
- `agent-collaboration`
- `reports-evidence`
- `internal-support`

## Cross-Field Rules

1. `kind=internal` requires `family=internal-support`, `status=internal`, and a
   `covered-by:` test reference.
2. `kind=cli` must not use `status=internal`.
3. `mode=read-only` requires `write_surface=none`, except explicitly selected
   report output makes the tool `proposal-only` rather than read-only.
4. `mode=approved-write` requires an `instruction` under `docs/runbooks/`.
5. Every `instruction`, `test`, and non-`none` `spec` target must exist.
6. The registry tool set must exactly equal the tracked `tools/*.py` set.
7. A tool appears in one primary family only. Cross-family relationships belong
   in family-guide links, not duplicate registry rows.
8. In a Git checkout, the expected tool set is the output of
   `git ls-files -- tools/*.py`; filesystem discovery is allowed only when the
   repository fixture has no Git metadata.
9. An `approved-write` row without a rollback-bearing runbook is a blocking
   finding. Its deterministic remediation path is `docs/runbooks/` followed by
   the Python filename stem and the `.md` extension.

## Structural Check Names

The existing audit result appends these stable checks:

| Check | Failure items |
|---|---|
| `tool_registry_document_present` | missing registry path or table header |
| `tool_registry_parseable` | malformed row and source line |
| `tool_registry_complete` | tracked tools absent from registry |
| `tool_registry_no_stale_entries` | registry tools absent from tracked set |
| `tool_registry_unique` | duplicate tool paths and line numbers |
| `tool_registry_required_fields` | empty `tool:field` pairs |
| `tool_registry_controlled_values` | invalid `tool:field=value` values |
| `tool_registry_cross_field_rules` | violated cross-field rule and tool |
| `tool_registry_references_exist` | missing `tool:field:path` targets |
| `instruction_tree_references_exist` | missing canonical instruction targets |

## Output Compatibility

Structural checks are represented as existing `DocLagCheck` records. The audit
keeps these top-level fields:

```json
{
  "status": "ok | lagging",
  "generated_utc": "ISO-8601 UTC timestamp",
  "repo": "absolute repository path",
  "checks": [],
  "findings": []
}
```

The CLI returns zero only when `status=ok`; it returns one for `lagging`.

## Safety Contract

- Parse tracked repository files only.
- Do not read the live vault, `out/` evidence bodies, services, credentials, or
  network resources.
- Findings may include repository paths and field names, never note contents or
  secret values.
- Secret-shape checks report only the repository-relative filename and stable
  check ID, never the matched line or value.
- Audit output remains under the caller-selected repository output directory.
