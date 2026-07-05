# 30 — Orchestrator Operating Spec

Status: active consolidation spec
Date: 2026-07-04
Scope: single operator-facing control document for continuing Obsidian Operating Layer work as an orchestrated, proposal-first system.

## Purpose

This document consolidates the current operating boundary that was previously spread across the orchestration backlog, Nanobot worker contract, Headroom channel policy, channel registry, and semantic proposal workflow.

It does not replace the detailed source specs. It is the first document Hermes should read when deciding the next safe action.

Source specs:

- `24-orchestration-backlog.md` — execution order and accepted backlog slices.
- `26-nanobot-standing-worker.md` — Nanobot standing worker contract.
- `28-global-headroom-only-llm-channel.md` — external LLM routing policy.
- `29-channel-registry.md` and `channel-registry.json` — machine-readable channel map.
- `29-semantic-proposal-workflow.md` — current semantic proposal/review pipeline.
- `31-operator-flow-and-review-queue.md` — explicit Agentic OS operator flow and evidence-gated review queue.
- `32-codex-hermes-communication-channel.md` — Codex task/report channel, roles, and rights.
- `33-codex-native-runtime.md` — native Codex runner and task/report runtime policy.
- `34-agentic-improvement-loop.md` — Nanobot/Hermes/Codex continuous improvement loop.

## Operating mode

Hermes works as orchestrator and acceptance owner:

1. observe current repo/vault/report state;
2. dispatch bounded workers only with explicit scope;
3. accept only evidence-backed outputs;
4. convert findings into proposal-only artifacts first;
5. request explicit approval before any live vault mutation;
6. backup, apply, and verify only after an approved manifest exists;
7. keep Nanobot/Codex improvement findings flowing through spec-kit, review queue, and bounded task packets.

Nanobot works as a supervised standing worker:

- allowed: observe, summarize, find docs lag, route task packets, draft proposal-only reports, review sanitized evidence;
- forbidden without explicit approval: live vault mutation, repo mutation outside a dispatched repo-doc task, auth/profile changes, service restarts, network exposure, cron changes beyond the approved scout, paid actions, and automatic embeddings.

## Channel rules

External LLM calls must go through Headroom. Local-only health checks, read-only gateways, systemd checks, and Ollama embeddings remain local traffic.

Accepted routes:

| Component | Route | Boundary |
|---|---|---|
| Hermes/Codex | Codex config provider `headroom`, `http://127.0.0.1:8787/v1` | coding/review under project rules |
| Codex communication channel | `~/.codex-hermes/comm/` via `tools/codex_hermes_comm.py` | task/report/ACK only; repo-scoped writes only when dispatched; Hermes verifies |
| Nanobot audit scout | `/home/hermesadmin/.nanobot-hermes/bin/nanobot-headroom-agent` | read-only/proposal-only; evidence via `http://127.0.0.1:18791/` |
| Graphify external extraction | `graphify-headroom` + Codex CLI backend | sandbox/report output only |
| Ollama embeddings | `127.0.0.1:11434` | local exception; bounded batches only |

If a route returns provider/auth/capacity errors, mark the worker blocked. Do not silently bypass Headroom or switch to raw provider credentials.

## Current workstream

The active product slice is the semantic proposal/review layer:

```text
Graphify/index evidence
  -> semantic query smoke / evidence bundle
  -> proposal-only semantic report
  -> candidate decision packet
  -> targeted semantic proposal
  -> semantic review index
  -> Nanobot/Hermes review
  -> optional future approval manifest after explicit approval
```

Current boundary:

- `live_mutation_authorized: false`
- no approval manifest unless explicitly requested;
- candidate paths are evidence inputs, not edit targets;
- generated artifacts stay under `out/proposals/` or `out/reports/`;
- live Obsidian apply remains closed.

## Orchestrator backlog now

1. Keep baseline green: `git diff --check`, targeted tests, and `make verify` when code/runtime changes.
2. Keep docs consolidated: update this spec and the source spec only when an accepted boundary changes.
3. Use Nanobot scout output as a second opinion, not as authority.
4. Promote proposal-only findings into small decision packets.
5. Promote accepted findings into the evidence-gated review queue before any manifest/apply step.
6. Keep the generated artifact pointers below current when new review/report indexes are emitted.
7. Do not move to live apply until Dmitry approves a named approval manifest.

## Current generated artifact pointers

These pointers are review inputs, not approval to apply. Refresh them when the semantic workflow emits a newer accepted artifact.

| Artifact class | Current pointer | Use |
|---|---|---|
| Semantic query report | `out/proposals/semantic-query-reports/final468-operator-review-20260704T093433Z/REPORT.md` | source proposal-only semantic evidence |
| Candidate decision packet | `out/proposals/semantic-candidate-decisions/final468-operator-review-20260704T105830Z/REPORT.md` | promoted candidate grouping for operator review |
| Targeted semantic proposal | `out/proposals/semantic-targeted-proposals/link-hygiene-20260704T112830Z/REPORT.md` | targeted proposal-only packet; no edit targets |
| Semantic review index | `out/proposals/semantic-review-indexes/link-hygiene-20260704T1200Z/REPORT.md` | accepted review index for link hygiene candidates |
| Operator decision packet | `out/proposals/operator-decision-packets/link-hygiene-20260704T153221Z/REPORT.md` | current promotion/hold decisions for semantic findings |
| Link hygiene evidence brief | `out/proposals/link-hygiene-evidence-briefs/20260704T154000Z/REPORT.md` | current proposal-only triage decision for link-hygiene findings |
| Non-report working-note wikilink triage | `out/proposals/non-report-working-note-wikilink-triage/20260704T154634Z/REPORT.md` | fresh current triage for non-sensitive working-note link-debt candidates; no edit targets |
| Working-note link targeted proposal | `out/proposals/working-note-link-targeted-proposals/20260704T155803Z/REPORT.md` | 102 proposal-only disambiguation candidates across 26 files; no live apply |
| Working-note link operator review | `out/proposals/working-note-link-operator-reviews/20260704T161938Z/REPORT.md` | 102 candidates approved for future manifest consideration, 3 held; no approval manifest or live apply |
| Working-note link manifest-candidate dry-run | `out/proposals/working-note-link-manifest-candidates/20260704T162439Z/REPORT.md` | 102 dry-run replacements across 26 files; named candidate only, no approval manifest or live apply |
| Working-note link live apply | `out/reports/working-note-link-apply/20260704T163336Z/REPORT.md` | Dmitry-approved apply of 102 working-note disambiguations across 26 files; backups and post-verify ok |
| Working-note link post-apply observation | `out/reports/working-note-link-post-apply-observation/20260704T164100Z/REPORT.md` | approved old links remaining 0; held items still excluded; next triage needed for remaining ambiguity |
| Held Reports README link apply | `out/reports/working-note-held-report-readme-apply/20260704T165519Z/REPORT.md` | 3 held report README links resolved by explicit Memory-Vault/Hermes/Reports domain rule; backups and post-verify ok |
| Post-held working-note wikilink triage | `out/reports/non-report-working-note-wikilink-post-held-triage/20260704T170534Z/REPORT.md` | fresh read-only scan after held-link apply; 286 remaining general working-note ambiguous issues; no live edits |
| Next safe working-note disambiguation proposal | `out/proposals/working-note-link-next-safe-disambiguation/20260704T170712Z/REPORT.md` | 231 proposal-only same-project/known-project rewrites across 41 files; 55 held; no approval manifest or live apply |
| Current link hygiene scan | `out/reports/link-hygiene-current-scan/20260704T-current-brief/REPORT.md` | read-only live-vault signal check; no mutation |
| Nanobot scout report | `out/reports/nanobot-cron-scout/20260704T152408Z/REPORT.md` | read-only second-opinion docs/project lag audit |
| Docs lag audit | `out/reports/project-docs-lag-audit/orchestrator-20260704T-live-apply/REPORT.md` and per-run Nanobot `docs-lag-audit/` | deterministic companion audit |

## Evidence gateway traversal

Nanobot and future scouts should begin from:

```text
http://127.0.0.1:18791/snapshot.json
```

Current high-value read-only evidence URLs:

- `http://127.0.0.1:18791/project-docs/acceptance/index.md`
- `http://127.0.0.1:18791/project-docs/spec-kit/24-orchestration-backlog.md`
- `http://127.0.0.1:18791/project-docs/spec-kit/26-nanobot-standing-worker.md`
- `http://127.0.0.1:18791/project-docs/spec-kit/28-global-headroom-only-llm-channel.md`
- `http://127.0.0.1:18791/project-docs/spec-kit/29-channel-registry.md`
- `http://127.0.0.1:18791/project-docs/spec-kit/29-semantic-proposal-workflow.md`
- `http://127.0.0.1:18791/project-docs/spec-kit/30-orchestrator-operating-spec.md`

If gateway paths return 404/403, treat that as gateway path-map evidence and update the gateway/index docs. Do not infer docs lag from a guessed URL alone.

## Acceptance standard

Every accepted slice must report:

- changed files;
- exact commands run;
- verification result;
- safety boundary;
- next blocker or next explicit approval needed.

## Block handling

If Nanobot, Graphify, Headroom, Codex, or another worker is blocked by provider/auth/capacity/runtime errors, Hermes records the blocker and continues only with deterministic local evidence. Worker failure does not authorize bypassing the channel policy or weakening the vault safety contract.


## Codex native runtime

Codex is made repo-native through `docs/spec-kit/33-codex-native-runtime.md`, `/home/hermesadmin/.codex-hermes/bin/hermes-codex-run`, schema-versioned task/report packets, and explicit separation from Nanobot's architecture scout channel. Nanobot may recommend Codex tasks; Hermes dispatches and accepts them.


## Agentic improvement loop

The continuous improvement loop is defined in `docs/spec-kit/34-agentic-improvement-loop.md`:

```text
Nanobot scout -> Hermes triage -> spec-kit/queue update -> bounded Codex review/implementation -> Hermes verification -> operator decision for gated actions
```

Nanobot can recommend improvements and candidate Codex tasks. Hermes collects and analyzes them. Codex can be run across the project in review-only mode, but usage/runtime/provider blockers are recorded as blockers, not bypassed.
