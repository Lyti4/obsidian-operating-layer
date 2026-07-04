# Channel Registry — Hermes / Codex / Headroom / Nanobot / Obsidian Layer

Status: proposal-active  
Source of truth: `docs/spec-kit/channel-registry.json`

This registry is the machine-readable map for inter-agent and tool channels. It exists to prevent silent drift in routing, permissions, and acceptance ownership.

Core rule: external LLM-provider traffic goes through Headroom by default. Local health checks, systemd, the read-only evidence gateway, and Ollama embeddings remain local traffic.

Safety invariant: Nanobot proposes; Hermes verifies and accepts/rejects; live vault mutation requires an explicit approval manifest.
