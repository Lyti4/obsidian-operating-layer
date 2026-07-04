# Acceptance Index — Obsidian Operating Layer

Status: current acceptance map  
Scope: source-of-truth summary for accepted, limited, and not-yet-accepted project capabilities.

## Accepted now

| Layer | Status | Evidence / source |
|---|---|---|
| Safety core | Accepted baseline | `docs/spec-kit/03-safety-contract.md`, tests, `make verify` |
| Observe/propose/verify/apply-dry-run | Accepted baseline | `README.md`, `docs/spec-kit/14-operational-acceptance-report.md` |
| Approval manifest binding | Accepted baseline | tests + apply policy in `AGENTS.md` |
| Protected path refusal | Accepted baseline | tests + safety contract |
| Review dashboard list/explain | Accepted baseline | `docs/obsidian-review-dashboard/index.md`, acceptance reports |
| Sandbox vault copies | Accepted baseline | `tools/obsidian_sandbox.py`, E2E evidence |
| Diagram/PDF report generation | Accepted with manual readability gate | `docs/spec-kit/15-manual-and-adapter-acceptance.md` |
| Controlled autonomy queue | Accepted only as explicit manual jobs | `docs/controlled-autonomy.md`; no scheduler installed |
| Indexing wrapper/runtime | Accepted for sandbox, guarded read-only probes, and final468 Graphify-derived semantic query smoke | `docs/spec-kit/20-indexing-runtime-acceptance.md`, `out/reports/graphify-final468-acceptance-20260704T065729Z/REPORT.md` |
| Semantic query proposal-only reports | Accepted as review-candidate path with empty `targets`, candidate notes, safety boundary, and no apply authorization | `tools/obsidian_semantic_proposal_report.py`, `tools/obsidian_review_dashboard.py explain`, `out/proposals/semantic-query-reports/final468-operator-review-20260704T093433Z/REPORT.md`, `EXPLANATION.md` |

## Limited / conditional

| Capability | Current boundary | Next gate |
|---|---|---|
| External MCP/RAG adapters | Sandbox/read-only/proposal-only | adapter-specific sandbox scorecard |
| Semantic indexing | Accepted for final468 sandbox/derived-cache pass and proposal-only candidate reports; no live vault mutation; no unattended routine job | explicit approval for any live apply |
| Live vault proposal generation | Read-only observation + proposal bundle | human review of proposal and manifest |
| Live apply | Not generally enabled | explicit approval manifest, backup, apply, verify |

## Not accepted yet

- Unreviewed live vault mutation.
- Direct write/delete/move by external MCP/RAG/plugin tools.
- Scheduling/cron/systemd for controlled autonomy.
- Routine unattended production semantic indexing without explicit schedule/resource approval.
- Any handling that prints or stores secrets in notes/reports.

## Required evidence for future acceptance

For each new accepted capability, add:

1. command(s) run;
2. exact artifact paths;
3. pass/fail result;
4. safety boundary statement;
5. rollback/disable path;
6. whether the live vault was mutated.

## Current operator default

When uncertain, treat the system as:

```text
read-only live vault + sandbox writes + proposal-only live changes
```

Live apply remains opt-in per proposal.
