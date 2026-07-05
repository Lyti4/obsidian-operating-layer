# 38 — Unified Queue / State / Decision Surface v1

Status: proposal-only surface draft
Date: 2026-07-05
Scope: unify queue state, lane schema, candidate scoring, decision ledger, proposal thresholds, and routing into one review-only boundary

## Purpose

This spec defines one coherent proposal-only boundary for the new control-plane primitives introduced by the vault-automation roadmap.

It exists to reduce navigation and implementation ambiguity. It does not authorize live apply, approval-manifest creation, or any mutation of the live vault.

## Boundary

- `live_mutation_authorized: false` is mandatory.
- Decision ledger entries remain weak evidence only.
- Routing outputs are disposition signals, not permission grants.
- Candidate scoring is evidence for proposal ranking, not an apply owner.
- Thresholds may permit proposal generation, but never live mutation.

## Unified contract

The surface combines five existing primitives:

| Primitive | Contract role |
|---|---|
| `lane_schema_v1` | Defines the lane packet shape and safety flags for a candidate class. |
| `candidate_scorer_v1` | Produces candidate rank, reason codes, and feature breakdowns for the lane. |
| `operator_decision_ledger_v1` | Stores weak evidence/prior decisions only; informs future scoring without authority. |
| `safe_auto_proposal_thresholds` | Decides whether dry-run proposal generation is safe for the candidate. |
| `proposal_routing_contract_v1` | Routes the candidate into `suggest`, `auto-propose`, `needs-human-review`, or `blocked/refuse`. |

## State model

Queue state is separate from routing disposition but lives in the same review surface.

| Queue state | Meaning |
|---|---|
| `observed` | Evidence exists, but the item has not been classified yet. |
| `triaged` | Hermes has assigned a risk/scope class. |
| `proposal_drafted` | A proposal-only artifact exists. |
| `review_ready` | The item can be reviewed with evidence, routing, and safety context attached. |
| `approved_for_manifest` | Dmitry has explicitly approved the exact candidate set. |
| `applied_verified` | A separately approved live apply has been backed up, applied, and post-verified. |
| `held` | The item is not safe or actionable yet. |
| `rejected` | The item is unsafe or not useful for this slice. |

## Contract boundary summary

The unified surface is valid only when all of the following remain true:

- queue state describes where an item is in the review flow;
- lane schema describes the item class and sensitive-surface flags;
- scorer explains candidate preference with reasons and features;
- ledger stays weak and non-authoritative;
- thresholds gate proposal generation only;
- routing emits operator-facing disposition only;
- live apply remains separate and opt-in.

## Acceptance

- proposal-only, no live mutation authorization;
- clear mapping between the five primitives above;
- explicit state model for review flow;
- machine-readable enough to support later generated indexes or dashboards;
- safe for inclusion in docs/indexes without introducing apply authority.
