# Runtime Status — Obsidian Operating Layer

This file records current operational runtime state. It is evidence/status, not acceptance by itself.

Verify current jobs/services before relying on these details.
Cron IDs/script paths here are operational evidence and may go stale; verify with current scheduler/service state before acting.

## Nanobot scheduled loop

The approved definitions still exist, but the current verified state on 2026-07-10 is paused:

| Job | Approved definition | Current state |
| --- | --- | --- |
| `212b7e8f3c21` | Scout every 15 minutes via `/home/hermesadmin/.hermes/scripts/nanobot_obslayer_scout.py`; local delivery and reports under `out/reports/nanobot-cron-scout/`. | Paused |
| `d2a5fd33b29f` | Lightweight reviewer every 15 minutes via `/home/hermesadmin/.hermes/scripts/nanobot_report_reviewer.py`; origin-chat delivery for new reviews and reports under `out/reports/nanobot-hermes-reviewer/`. | Paused |
| `835d51562f73` | Companion deep reviewer every 4 hours via `/home/hermesadmin/.hermes/scripts/nanobot_deep_review_companion.py`; bounded `companion` batches and reports under `out/reports/nanobot-companion-deep-review/`. | Paused |

Verify with `hermes cron list --all` before relying on this table. This repo-only slice does not resume the jobs.

All jobs are bounded read-only/proposal-only. The scout uses a lock/timeout, the evidence gateway, and the Headroom bridge. The lightweight reviewer only reads Nanobot reports, tracks reviewed hashes, summarizes action signals, and must not change repo/vault/auth/profile/services/network/embeddings. The companion deep reviewer is for proposal-only classification of old/new reports (`duplicate`, `no-action`, `stale`, `actionable`, `blocker`) and must not mutate repo/vault/auth/profile/services/network/embeddings, close docs/cards, or apply changes. Reports are evidence; Hermes/Dmitry acceptance is still required before closing docs/cards or applying changes.

## Hermes memory bridge

`tools/hermes_obslayer_memory.py` is a tracked read-only lexical fallback over Markdown notes. It is not yet an active Hermes `MemoryProvider`, automatic capture path, or semantic indexer; those remain later separately accepted slices.
