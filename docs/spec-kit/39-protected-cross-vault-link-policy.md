# Protected cross-vault link policy

Status: accepted after generated-report noise cleanup on 2026-07-06.

## Problem

Some active Memory-Vault reports intentionally reference protected Soul notes through paths such as `Hermes/Soul/...`. These are not generated-report garbage, but they also must not cause bulk mutation of Memory-Vault or scanning of Soul-Vault as ordinary memory notes.

## Policy

1. A protected bridge may resolve links when it is explicitly mounted in the active vault, for example `Memory-Vault/Hermes/Soul -> Soul-Vault/Soul`.
2. The observer may treat such bridge targets as resolved links, but must not expand the protected target vault into the active note inventory.
3. Protected bridge targets are read-only from the Memory-Vault cleanup lane. Do not rewrite, move, create, or delete Soul notes from Obsidian link hygiene tasks.
4. If a protected target is absent, leave it in manual-review/protected policy bucket. Do not auto-create placeholder notes in Memory-Vault.
5. Report-only examples that mention protected paths should still be rendered as literals or code when they are examples, not live memory references.

## Current baseline

With the generated-report noise policy and protected bridge behavior:

```text
observe_vault('/home/hermesadmin/Obsidian/Memory-Vault')
notes: 313
broken_links: 0
orphans: 113
duplicates: 2
```

The earlier 7 unresolved items were protected `Hermes/Soul/...` references. They are now considered resolved only through the explicit protected bridge, not by importing Soul-Vault into the active Memory-Vault index.

## Regression coverage

`tests/test_obslayer.py::test_observe_vault_resolves_protected_symlink_without_scanning_it` verifies that a symlinked protected target can satisfy a link while the observer keeps the protected vault out of the active note list.
