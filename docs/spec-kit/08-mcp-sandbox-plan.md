# MCP Sandbox Plan

## Goal

Evaluate ready Obsidian MCP servers as read/search/graph/propose components while preventing direct live writes.

## Candidate order

1. `cyanheads/obsidian-mcp-server` — primary broad MCP candidate.
2. `rps321321/obsidian-mcp-pro` — graph/canvas/link-analysis rich candidate.
3. `bettyguo/obsidian_mcp` — Python-friendly candidate for simpler glue.

## Sandbox setup

```text
live vault -> copied test vault -> MCP server -> adapter wrapper -> findings/proposals
```

Never point first-run MCP evaluation at live writable vault.

## Required checks per candidate

- README install/run command.
- License.
- Runtime and dependencies.
- Can it run on a copied vault?
- Can write tools be disabled by config, permissions, or wrapper?
- Which tools are safe: read/search/frontmatter/tags/links/graph?
- Which tools are dangerous: write/edit/delete/move?
- Does output preserve relative paths and evidence?

## Wrapper policy

The adapter exposes only:

```json
["read", "search", "graph", "metadata-read", "write-request"]
```

It blocks:

```json
["write-direct", "delete-direct", "move-direct"]
```

If the MCP server has built-in write tools, wrapper must either disable them or run with filesystem permissions that cannot write to live vault.

## Sandbox acceptance test

1. Copy a small sample vault to `out/sandbox-vaults/mcp-*`.
2. Start candidate MCP server against sandbox copy.
3. Run read/search/link-analysis calls.
4. Attempt a write-like request and verify it becomes proposal or is refused.
5. Confirm live vault unchanged.
6. Save report under `out/reports/mcp-sandbox-*.md`.

## Promotion criteria

A candidate can move to adapter implementation only if:

- read/search works;
- direct live write path is disabled/refused;
- findings have enough evidence for human review;
- adapter can emit obslayer-compatible finding/proposal JSON;
- risks are documented.
