# 48 — Candidate Volume Operator Packet

Status: implemented repo-only operator gate
Date: 2026-07-06

## Purpose

`candidate-volume-operator-packet-v1` summarizes candidate volume, protected-path exposure, proposal target count, verification state, and unified-index readiness before any live pilot is considered.

It is evidence-only and proposal-only. It is not an approval manifest, does not create one, and grants no apply authority.

## Inputs

The builder consumes four existing repo-local JSON artifacts:

- `observation.json`
- `proposal.json`
- `verify.json`
- `unified-operator-review-index.json`

Inputs must resolve inside the repository under `out/` or `docs/`. Symlink escapes are refused.

## Output

The CLI writes:

- `candidate-volume-operator-packet.json`
- `REPORT.md`

The packet includes fixed inert safety, `vault_root`, `observed_at`, file counts, protected hit volume and bucket counts, sample note count, proposal summary, verify summary, unified-index summary, and route buckets.

The fixed safety block is always:

```json
{
  "live_mutation_authorized": false,
  "approval_manifest_created": false,
  "approval_manifest_authority": false,
  "apply_authority": "none",
  "target_paths": []
}
```

## Status Rules

- `blocked`: any input claims live mutation, approval manifest creation/authority, non-`none` apply authority, failed verify evidence, or blocked unified artifacts.
- `ready_for_operator_review`: no blockers are present.

Non-empty proposal targets are routed to manual review only and never copied into `target_paths`. The `first_manifest_candidate_queue` stays empty unless a future slice explicitly defines safe target candidates.

## CLI

```bash
python3 tools/obsidian_candidate_volume_operator_packet.py \
  --repo . \
  --out-dir out/reports/candidate-volume-operator-packet/full-vault-proposal-only-20260706T182612Z
```

The current smoke artifact is generated only from existing repo-local JSON evidence under `out/live-proposal-only-20260706T182612Z/` and `out/reports/unified-operator-review-index/full-vault-proposal-only-20260706T182612Z/`.

Current result: `ready_for_operator_review`; protected hits `447`; proposal targets `0`; `first_manifest_candidate_queue: []`; fixed inert safety is mirrored at root level and under `safety` for unified gate compatibility. The packet JSON, report, and this spec are included in the regenerated self-contained full-vault unified operator review index, which now has 0 missing pointers.
## Follow-on Selector

`docs/spec-kit/49-manifest-candidate-selector.md` consumes this candidate-volume packet together with the unified index and operator review packet. It selects at most five review candidates for human review only and keeps `first_manifest_candidate_queue` empty here by design.
