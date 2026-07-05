# 29 — Semantic Proposal Workflow

Status: active proposal-only workflow
Updated: 2026-07-04

## Purpose

Make the completed semantic/indexing work discoverable as a safe review pipeline. This workflow turns Graphify/index evidence into proposal artifacts and operator decision packets without mutating the live vault.

## Boundary

- Live vault mutation is forbidden in this workflow.
- Nanobot may review only sanitized evidence through the read-only evidence gateway.
- Hermes remains acceptance owner.
- Any future apply requires a separate explicit approval manifest, backup, apply, and verify cycle.

## Flow

```text
Graphify/index evidence
  -> semantic query smoke / evidence bundle
  -> proposal-only semantic report
  -> candidate decision packet
  -> targeted semantic proposal
  -> Nanobot/Hermes review
  -> optional future approval manifest (separate explicit approval only)
```

## Current artifacts

- Proposal report CLI: `tools/obsidian_semantic_proposal_report.py`
- Decision packet CLI: `tools/obsidian_semantic_candidate_decision_packet.py`
- Targeted proposal CLI: `tools/obsidian_semantic_targeted_proposal.py`
- Review index CLI: `tools/obsidian_semantic_review_index.py`
- Review dashboard explain CLI: `tools/obsidian_review_dashboard.py explain`

Generated artifacts stay under:

```text
out/proposals/semantic-query-reports/
out/proposals/semantic-candidate-decisions/
out/proposals/semantic-targeted-proposals/
out/proposals/semantic-review-indexes/
```

## Acceptance checks

For code/workflow changes in this path, run:

```bash
pytest tests/test_semantic_proposal_report.py tests/test_semantic_candidate_decision_packet.py tests/test_semantic_targeted_proposal.py -q
make verify
git diff --check
```

For generated proposal artifacts, acceptance means:

- `live_mutation_authorized: false`
- no approval manifest unless explicitly requested
- clear source proposal/evidence path
- clear target count and candidate count
- readable operator report

## Related specs

- `24-orchestration-backlog.md`
- `25-nanobot-graphify-worker.md`
- `26-nanobot-standing-worker.md`
- `27-graphify-nanobot-embedding-orchestration.md`
- `28-global-headroom-only-llm-channel.md`
- `29-channel-registry.md`

## Targeted proposal explanation

Targeted semantic proposals may omit classic apply fields such as `approval_required` and `dry_run_default` when all of the following hold:

- `mode` starts with `semantic-`;
- `targets: []`;
- `live_mutation_authorized: false`;
- `safety.proposal_only: true`.

`tools/obsidian_review_dashboard.py explain` must render their `candidate_paths`, `proposed_changes`, and source decision packet as review inputs only.

## Review index step

A semantic review index is the first artifact after a targeted proposal packet. It lists promoted candidate source paths and the review disposition without reading or mutating the live vault.

Command:

```bash
make semantic-review-index \
  SEMANTIC_REVIEW_INDEX_PROPOSAL_JSON=out/proposals/semantic-targeted-proposals/link-hygiene-20260704T112830Z/proposal.json \
  SEMANTIC_REVIEW_INDEX_OUT=out/proposals/semantic-review-indexes/link-hygiene-manual
```

Acceptance:

- `live_mutation_authorized: false`
- `approval_manifest_created: false`
- no edit targets
- candidate paths are evidence inputs only

## Semantic/indexing manifest step

The terminal index artifact for the current semantic/indexing chain is a semantic manifest. It validates and summarizes the generated evidence chain without promoting `out/` artifacts into tracked source files.

Command:

```bash
make semantic-manifest
```

Default chain:

```text
graphify embedding manifest
  -> bounded embedding run
  -> query smoke
  -> semantic query proposal
  -> candidate decision packet
  -> targeted semantic proposal
  -> semantic review index
  -> semantic indexing manifest
```

Outputs stay under:

```text
out/reports/semantic-manifests/
```

Acceptance:

- `mode: semantic-indexing-manifest`
- `live_mutation_authorized: false`
- `approval_manifest_created: false`
- all referenced artifacts are under repo `out/`
- semantic proposal artifacts have empty `targets`
- findings are empty before the chain is considered ready for operator review

CLI: `tools/obsidian_semantic_manifest.py`
Library: `src/obslayer/semantic_manifest.py`
