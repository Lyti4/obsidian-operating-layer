# Runbook — Sandbox Indexing Probe

**Статус:** `active sandbox`. Governing family:
`docs/tools/families/indexing-graphify-semantic.md`. Current provider/service
state is not copied here; verify `docs/RUNTIME_STATUS.md`.

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

## Rollback

Stop the external process and remove only the named sandbox/derived root owned
by the failed run after checking its resolved path. Never clean the live vault,
shared cache or another run's evidence as sandbox rollback.
