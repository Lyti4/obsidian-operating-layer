# 36 — Current Evidence Index

Status: active evidence index
Date: 2026-07-05
Scope: tracked source index for current proposal-only/operator evidence pointers that would otherwise bloat acceptance or backlog docs.

## Purpose

Keep `docs/acceptance/index.md` and `docs/spec-kit/24-orchestration-backlog.md` concise while preserving reviewable pointers to the current generated reports/proposals under `out/`.

This document is an index only. It does not promote generated artifacts to source-of-truth status and does not authorize live mutation.

## Control-plane source surfaces

- First-read orchestrator spec: `docs/spec-kit/30-orchestrator-operating-spec.md`
- Operator flow / review queue: `docs/spec-kit/31-operator-flow-and-review-queue.md`
- Codex ⇄ Hermes channel: `docs/spec-kit/32-codex-hermes-communication-channel.md`, `tools/codex_hermes_comm.py`, `~/.codex-hermes/docs/ROLE_POLICY.json`
- Codex native runtime: `docs/spec-kit/33-codex-native-runtime.md`, `tools/hermes_codex_run.py`
- Agentic improvement loop: `docs/spec-kit/34-agentic-improvement-loop.md`
- Agentic OS control plane map: `docs/spec-kit/35-agentic-os-control-plane-map.md`
- Semantic workflow: `docs/spec-kit/29-semantic-proposal-workflow.md`
- Channel registry: `docs/spec-kit/29-channel-registry.md`, `docs/spec-kit/channel-registry.json`

## Current generated evidence pointers

These paths are generated artifacts and stay ignored by git unless a future review explicitly promotes a distilled source document.

- Semantic query report: `out/proposals/semantic-query-reports/final468-operator-review-20260704T093433Z/REPORT.md`
- Candidate decision packet: `out/proposals/semantic-candidate-decisions/final468-operator-review-20260704T105830Z/REPORT.md`
- Targeted semantic proposal: `out/proposals/semantic-targeted-proposals/link-hygiene-20260704T112830Z/REPORT.md`
- Semantic review index: `out/proposals/semantic-review-indexes/link-hygiene-20260704T1200Z/REPORT.md`
- Semantic indexing manifest: `out/reports/semantic-manifests/manual/REPORT.md`
- Operator decision packet: `out/proposals/operator-decision-packets/link-hygiene-20260704T153221Z/REPORT.md`
- Link hygiene evidence brief: `out/proposals/link-hygiene-evidence-briefs/20260704T154000Z/REPORT.md`
- Non-report working-note wikilink triage: `out/proposals/non-report-working-note-wikilink-triage/20260704T154634Z/REPORT.md`
- Working-note link targeted proposal: `out/proposals/working-note-link-targeted-proposals/20260704T155803Z/REPORT.md`
- Working-note link operator review: `out/proposals/working-note-link-operator-reviews/20260704T161938Z/REPORT.md`
- Working-note link manifest-candidate dry-run: `out/proposals/working-note-link-manifest-candidates/20260704T162439Z/REPORT.md`
- Working-note link live apply: `out/reports/working-note-link-apply/20260704T163336Z/REPORT.md`
- Working-note link post-apply verification: `out/reports/working-note-link-post-apply-verify/20260704T163336Z/REPORT.md`
- Working-note link post-apply observation: `out/reports/working-note-link-post-apply-observation/20260704T164100Z/REPORT.md`
- Held Reports README link apply: `out/reports/working-note-held-report-readme-apply/20260704T165519Z/REPORT.md`
- Post-held working-note wikilink triage: `out/reports/non-report-working-note-wikilink-post-held-triage/20260704T170534Z/REPORT.md`
- Next safe working-note disambiguation proposal: `out/proposals/working-note-link-next-safe-disambiguation/20260704T170712Z/REPORT.md`
- Current link hygiene read-only scan: `out/reports/link-hygiene-current-scan/20260704T-current-brief/REPORT.md`
- Latest accepted Nanobot scout sample: `out/reports/nanobot-cron-scout/20260704T152408Z/REPORT.md`
- Nanobot all-reports aggregate: `out/reports/nanobot-all-reports-aggregate-20260705.md`

## Safety boundary

- Proposal-only/read-only unless a separate approval manifest says otherwise.
- `live_mutation_authorized: false` for this index.
- No approval manifest is created by this index.
- Do not edit live vaults, services, auth/profile state, cron, network exposure, or public/p paid surfaces from these pointers.
