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
