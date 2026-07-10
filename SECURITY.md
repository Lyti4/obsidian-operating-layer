# Security Policy

## Supported versions

The `main` branch is the active supported line.

## Reporting a vulnerability

Do not open public issues with secrets, tokens, credentials, private vault content, browser profiles, cookies, or private keys.

Use GitHub private vulnerability reporting when available, or contact the repository owner directly with a minimal, sanitized report.

## Project safety boundaries

- Read-only-first by default.
- Live Obsidian mutation requires an explicit approval manifest, backup, apply, and verify sequence.
- Protected paths stay protected: `.obsidian`, `_Backups`, `_Archive`, `.trash`, and Soul-protected areas.
- External adapters must remain sandbox-only or proposal-only unless explicitly approved.

## Instruction authority

Security boundaries originate in `AGENTS.md` and are mapped in
`docs/INSTRUCTION_TREE.md`. Nested files such as `tools/AGENTS.md`,
`src/obslayer/AGENTS.md`, `tests/AGENTS.md`, and `docs/agents/AGENTS.md` may
narrow those boundaries but must not weaken them.

A security-relevant code, tool, workflow, runtime, or role change updates the
affected canonical/active documentation in the same slice. Reports must not
contain secret values, private URLs, credentials, or live note bodies.
