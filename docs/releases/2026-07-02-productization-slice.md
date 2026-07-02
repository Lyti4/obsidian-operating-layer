# Release Note — 2026-07-02 Productization Slice

Status: docs/productization slice

## Scope

Adds a clearer operational release surface for Obsidian Operating Layer:

- release readiness gate;
- acceptance index;
- short operator runbooks.

## Safety boundary

No live Obsidian vault mutation is approved by this slice.

## Verification

Run before accepting this slice:

```bash
make verify
git diff --check
```

## Next intended slice

Stabilize the indexing runtime workflow with a medium sandbox probe, then update acceptance evidence.

## P2 medium sandbox probe update

- Ran fake stdio wrapper probe: green.
- Ran real `@dalecb/obsidian-semantic-mcp@0.2.1` medium sandbox probe against 10 small Markdown files, batch size 2: green.
- Used scoped Node 24 wrapper; did not update global/user Node.
- Verified sanitized transcript redactions and no recent live vault modification.
