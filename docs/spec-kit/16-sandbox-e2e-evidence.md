# Sandbox E2E Evidence

## Purpose

This document records the safe server-side E2E pass after P3 operator polish. It is an evidence index, not an approval to mutate the real Obsidian vault.

## Scope

Covered safe flows:

- sandbox vault creation under `out/sandbox-vaults/`;
- smoke dry-run / proposal style flow;
- field-slice proposal-only flow;
- review dashboard `list` and `explain` read-only commands;
- diagram render into approved `out/diagrams/` and `out/reports/` paths;
- RAG sandbox benchmark on copied notes;
- MCP sandbox benchmark with dangerous write refusal;
- apply refusal when no approval manifest is provided;
- full repository verification after generated artifacts.

Not covered:

- no live apply to `/home/hermesadmin/Obsidian`;
- no cron/systemd/scheduler installation;
- no public/network exposure or production deploy.

## Latest safe E2E pass

Status: accepted for sandbox/read-only operation.

Evidence directories from the safe E2E run:

```text
out/e2e-safe-20260628-112852Z
out/sandbox-vaults/e2e-20260628-112852Z
out/diagrams/e2e-20260628-112852Z
out/reports/e2e-20260628-112852Z
```

Observed results:

```text
smoke dry-run                 OK
field-slice proposal-only      OK
dashboard list                 OK
dashboard explain              OK
diagram bad-dir guardrail      OK, refused unsafe output path
diagram render allowed dir     OK, SVG/PDF created under approved out paths
RAG benchmark sandbox          OK, notes_scanned=2
MCP benchmark sandbox          OK, dangerous_tools_refused=true
apply without manifest         OK, refused with exit_code=2
```

Refusal evidence:

```text
error: Live apply requires --approval-manifest
```

Diagram path guardrail evidence:

```text
Diagram outputs must stay under .../out/diagrams
```

Post-run repository verification:

```text
make verify
pytest 70 passed
ruff passed
compileall OK
```

Repository state after the pass:

```text
HEAD 0466686 Add P3 operator polish
git status clean
```

## Safe reproduction commands

Use these commands only against disposable/sandbox data unless Dmitry explicitly approves a live scope.

```bash
make verify
make dashboard-list
make field-slice-example
make render-diagrams
make rag-benchmark
make mcp-benchmark
```

For apply refusal checks, do not provide an approval manifest:

```bash
python3 tools/obsidian_apply.py --proposal out/proposals/example/proposal.json --apply
```

Expected result: refusal because real apply requires `--approval-manifest`.

## Acceptance decision

The system is accepted for safe sandbox/read-only/proposal-only operation after P3 polish.

Remaining actions require separate explicit approval:

1. real live apply to a named vault scope;
2. cron/systemd/scheduled observe/index reports;
3. optional visual theme expansion beyond the current accepted Mermaid theme variables.
