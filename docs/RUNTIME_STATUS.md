# Runtime Status — Obsidian Operating Layer

This file records current operational runtime state. It is evidence/status, not acceptance by itself.

Verify current jobs/services before relying on these details.
Cron IDs/script paths here are operational evidence and may go stale; verify with current scheduler/service state before acting.

## Nanobot scheduled loop

Approved scheduled Nanobot loop:

- Scout: Hermes cron job `212b7e8f3c21` runs every 15 minutes via `/home/hermesadmin/.hermes/scripts/nanobot_obslayer_scout.py`, local delivery only, with reports under `out/reports/nanobot-cron-scout/`.
- Hermes lightweight reviewer: Hermes cron job `d2a5fd33b29f` runs every 15 minutes via `/home/hermesadmin/.hermes/scripts/nanobot_report_reviewer.py`, delivers to the origin chat only when new Nanobot reports are reviewed, and writes digests under `out/reports/nanobot-hermes-reviewer/`.
- Companion deep reviewer: Hermes cron job `835d51562f73` runs every 4 hours via `/home/hermesadmin/.hermes/scripts/nanobot_deep_review_companion.py`, invokes the separate low-usage profile `companion` with bounded batches, drains old Nanobot scout reports, delivers to the origin chat, and writes deep-review artifacts under `out/reports/nanobot-companion-deep-review/` with state in `~/.nanobot-hermes/comm/state/companion_deep_reviewer.json`.

All jobs are bounded read-only/proposal-only. The scout uses a lock/timeout, the evidence gateway, and the Headroom bridge. The lightweight reviewer only reads Nanobot reports, tracks reviewed hashes, summarizes action signals, and must not change repo/vault/auth/profile/services/network/embeddings. The companion deep reviewer is for proposal-only classification of old/new reports (`duplicate`, `no-action`, `stale`, `actionable`, `blocker`) and must not mutate repo/vault/auth/profile/services/network/embeddings, close docs/cards, or apply changes. Reports are evidence; Hermes/Dmitry acceptance is still required before closing docs/cards or applying changes.
