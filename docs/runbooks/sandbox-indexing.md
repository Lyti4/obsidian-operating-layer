# Runbook — Sandbox Indexing Probe

Use this before any larger semantic/MCP indexing work.

## Boundary

- Sandbox vault only.
- Derived index/cache outside the vault.
- No live vault mutation.
- Sanitized reports must redact live/sandbox/derived absolute paths and secrets.

## Basic verification

```bash
make verify
make indexing-runtime-stdio-probe-fake
```

## Medium probe rule

Before full indexing, run a bounded medium sandbox probe and confirm:

- no timeout;
- failed files are explained;
- sanitized transcript exists;
- live vault fingerprint is unchanged;
- tool surface matches the allowlist.

## Stop conditions

- timeout repeats without a sanitized partial report;
- live vault path appears in sanitized output;
- secret/env data leaks;
- external tool declares new write/delete/move capability;
- any live vault file changes.
