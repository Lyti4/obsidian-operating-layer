# Channel Registry — Hermes / Codex / Headroom / Nanobot / Obsidian Layer

Status: proposal-active  
Source of truth: `docs/spec-kit/channel-registry.json`

This registry is the machine-readable map for inter-agent and tool channels. It exists to prevent silent drift in routing, permissions, and acceptance ownership.

Core rule: external LLM-provider traffic goes through Headroom by default. Local health checks, systemd, the read-only evidence gateway, and Ollama embeddings remain local traffic.

Safety invariant: Nanobot proposes; Hermes verifies and accepts/rejects; live vault mutation requires an explicit approval manifest.

## Approved Nanobot scheduled scout

Dmitry approved one bounded Nanobot cron on 2026-07-04. The approved job is local-delivery only and uses `/home/hermesadmin/.hermes/scripts/nanobot_obslayer_scout.py` to run a daily read-only/proposal-only Obsidian Operating Layer scout.

Constraints:

- evidence access only through `http://127.0.0.1:18791/`;
- external LLM access only through `/home/hermesadmin/.nanobot-hermes/bin/nanobot-headroom-agent` and the Headroom backend Codex bridge;
- reports only under `out/reports/nanobot-cron-scout/`;
- no live vault/repo mutation, no auth/profile mutation, no service restart, no network exposure, no embedding auto-run;
- schedule/scope/delivery changes require a new explicit user approval.
