# Manual Review Selector Pipeline (v1)

## Scope

This document defines the **manual review selector v1** packet and packet-producing helper.
It is scoped to repo-only/evidence-only safety posture and should only emit
read-only review data for operator triage.

## Inputs

- Candidate packet from `obslayer.candidate_scorer_v1`
  (`scored_links` + per-link candidate payloads)
- Safe-auto threshold packet from `obslayer.safe_auto_proposal_thresholds_v1`
  (`held_for_review`, optionally with `source_candidate_scorer_packet`)

## Output packet contract

The function returns a JSON object with these required guardrails:

- `live_mutation_authorized: false`
- `approval_manifest_created: false`
- `approval_manifest_authority: false`
- `apply_authority: "none"`
- `targets: []`

and one of the status values:

- `ready_for_manual_review`
- `no_candidate`
- `blocked`

`blocked` is reserved for packet-level authority/safety violations only.

### Item schema (`review_items`)

Each emitted review item includes:

- `source`
- `old_link`
- `proposed_path`
- `confidence`
- `score`
- `top_two_gap`
- `route_hint`
- `reason_codes`
- `review_reason`
- `source_policy`, `classification`, `risk`, `apply_authority` from
  `docs/spec-kit/44-external-autograph-policy-adapter.md` when policy rules are
  applied
- `policy_tag` (always `manual-review-only`)
- `policy_taxonomy` (`authority`, `route_class`, `decision_class`, `apply_authority`)
- `candidate_count`, `top_score`, `thresholds`
- `source_provenance` preserving original route, hard-stop flag, reason codes, and safety flags
- internal `rank_features` used for stable sorting

## Selection rules

1. Links with `route_hint` in `{needs-human-review, suggest}` are considered directly.
2. Links with `route_hint=blocked/refuse` may be salvaged only as `manual-review-only` when the top candidate is safe, active, exact, above score/gap thresholds, and the original blocked/refuse provenance is preserved.
3. Hard reject causes are separated from soft/threshold reject causes in diagnostics.
4. Candidates with `hard_stop` or `hard_stop`-adjacent reasons/flags are skipped unless they are lower-ranked aggregate evidence preserved only as provenance for a safe top candidate.
5. Paths touching protected / sensitive surfaces are skipped:
   - Soul-related paths and notes
   - `_Archive`, `_Backups`, `.trash`
   - canonical/global/cached/redirected duplicate targets
   - generated report/noise targets under report output paths
6. Candidate confidence, score, top-two-gap, candidate count, and thresholds are retained for ranking and display.
7. Items are ranked with preference for:
   - `needs-human-review` over `suggest`
   - Memory surface (`Memory-Vault/...`)
   - `active_target_available`
   - `exact_title_match` / `alias_match`
   - confidence, score, and top-two-gap hints
8. Only top `max_candidates` are included.
9. Summary includes batching metadata: total accepted candidate pool, recommended initial sample size, and manual-review-only batch windows.

## CLI

Use:

```bash
python tools/obsidian_manual_review_selector.py \
  --proposal-json /path/to/input.json \
  --out-dir /tmp/manual-review-selector \
  --max-candidates 8
```

Generated artifacts:

- `manual-review-selector-v1.json`
- `manual-review-items.jsonl`
- `REPORT.md`

## Remaining-link suppression gate

Accepted follow-up policy: see `docs/spec-kit/45-remaining-link-suppression-gate.md`.

Known generated/report/protected/Graphify-exact unresolved links must be triaged with `tools/obsidian_remaining_link_triage.py` and passed to `tools/obsidian_candidate_scorer.py --suppression-triage-json ...` before building new review/apply queues. This prevents historical evidence links from repeatedly surfacing as actionable work while preserving audit artifacts and `apply_authority: none`.
