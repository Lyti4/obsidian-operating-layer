# 2026-07-04 — Nanobot scheduled scout approval

Dmitry approved one supervised Nanobot cron for Obsidian Operating Layer maintenance.

Implementation boundary:

- Hermes cron local delivery only;
- script: `/home/hermesadmin/.hermes/scripts/nanobot_obslayer_scout.py`;
- reports: `out/reports/nanobot-cron-scout/`;
- evidence reads only through `http://127.0.0.1:18791/`;
- external LLM route only through `nanobot-headroom-agent -> Headroom backend Codex bridge`;
- no live vault mutation, repository mutation by Nanobot, auth/profile mutation, service restart, network exposure, deploy, paid/high-volume action, or embedding auto-run.

Schedule, scope, delivery, or additional cron jobs require separate explicit approval.
