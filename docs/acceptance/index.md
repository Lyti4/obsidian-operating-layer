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
| Semantic targeted proposal/review index | Accepted as proposal-only operator review path; candidate paths are evidence inputs, not edit targets | `tools/obsidian_semantic_targeted_proposal.py`, `tools/obsidian_semantic_review_index.py`, `docs/spec-kit/29-semantic-proposal-workflow.md` |
| Semantic indexing manifest | Accepted as the terminal proposal-only index over generated Graphify/embedding/query/proposal/review artifacts; validates empty targets and no live mutation authorization | `tools/obsidian_semantic_manifest.py`, `src/obslayer/semantic_manifest.py`, `docs/spec-kit/29-semantic-proposal-workflow.md` |
| Proposal routing contract v1 | Accepted as routing-only classifier for `suggest` / `auto-propose` / `needs-human-review` / `blocked/refuse`; decision ledger remains weak evidence only and does not grant apply authority | `src/obslayer/proposal_routing_contract_v1.py`, `tests/test_proposal_routing_contract_v1.py`, `docs/spec-kit/31-operator-flow-and-review-queue.md`, `docs/spec-kit/37-vault-automation-indexing-roadmap.md` |
| Unified queue/state/decision surface v1 | Proposal-only boundary under design; unifies queue state, lane schema, scorer, ledger, thresholds, and routing, but preserves `live_mutation_authorized: false` | `docs/spec-kit/31-operator-flow-and-review-queue.md`, `docs/spec-kit/37-vault-automation-indexing-roadmap.md`, `docs/spec-kit/36-current-evidence-index.md` |
| Orchestrator operating spec | Accepted as first-read operator consolidation; does not replace source specs or authorize live apply | `docs/spec-kit/30-orchestrator-operating-spec.md`, `docs/spec-kit/00-overview.md`, `docs/spec-kit/24-orchestration-backlog.md` |
| Operator flow / review queue | Accepted as proposal-only coordination contract; queue states do not authorize live apply | `docs/spec-kit/31-operator-flow-and-review-queue.md`, `tools/obsidian_operator_review_queue.py`, `docs/spec-kit/30-orchestrator-operating-spec.md` |
| Codex ⇄ Hermes communication channel | Accepted as local task/report/ACK protocol with explicit rights; no cron installed by default; Hermes verifies Codex outputs | `docs/spec-kit/32-codex-hermes-communication-channel.md`, `tools/codex_hermes_comm.py`, `~/.codex-hermes/docs/ROLE_POLICY.json` |
| Agentic improvement loop | Accepted as proposal-first operating contract: Nanobot scouts, Hermes triages/specs/queues, Codex reviews or implements bounded repo tasks, Hermes verifies | `docs/spec-kit/34-agentic-improvement-loop.md`, `~/.codex-hermes/comm/hermes-inbox/agentic-os-project-wide-review-20260704.wrapper-20260704T193616Z.report.json` |
| Agentic OS control plane map | Accepted as canonical operator index for orchestrator/review-queue/Codex-Hermes/runtime/acceptance/docs-lag surfaces; documentation only, no live apply authorization | `docs/spec-kit/35-agentic-os-control-plane-map.md`, `docs/spec-kit/00-overview.md`, `src/obslayer/project_docs_lag_audit.py` |
| R7 narrow approved apply pilot | Accepted for the single reviewed archive-duplicate wikilink packet only; not a standing live-apply authorization | `out/proposals/working-note-link-archive-duplicate-live-apply/20260705T083603Z/approval-manifest.json`, `APPLY_REPORT.md`, backup `/home/hermesadmin/Obsidian/_Backups/obsidian-operating-layer/20260705-083637Z` |

## Limited / conditional

| Capability | Current boundary | Next gate |
|---|---|---|
| External MCP/RAG adapters | Sandbox/read-only/proposal-only | adapter-specific sandbox scorecard |
| Semantic indexing | Accepted for final468 sandbox/derived-cache pass and proposal-only candidate reports; no live vault mutation; no unattended routine job | explicit approval for any live apply |
| Live vault proposal generation | Read-only observation + proposal bundle | human review of proposal and manifest |
| Live apply | Single R7 packet accepted/applied; not generally enabled | new explicit approval manifest, backup, apply, verify per future packet |

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

## Current semantic/orchestrator evidence pointers

Current generated report/proposal pointers live in `docs/spec-kit/36-current-evidence-index.md` so this acceptance page stays concise. The index is proposal-only/read-only and does not authorize live mutation.

## Codex native runtime

Codex is made repo-native through `docs/spec-kit/33-codex-native-runtime.md`, `/home/hermesadmin/.codex-hermes/bin/hermes-codex-run`, schema-versioned task/report packets, and explicit separation from Nanobot's architecture scout channel. Nanobot may recommend Codex tasks; Hermes dispatches and accepts them.
