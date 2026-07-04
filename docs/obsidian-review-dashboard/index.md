---
title: Obsidian Review Dashboard
phase: 7
status: proposed
tags:
  - obslayer/review-dashboard
  - obslayer/phase-07
write_policy: proposal_only
---

# Obsidian Review Dashboard

This note is a Dataview-friendly dashboard source for reviewing Obsidian Operating Layer tasks, proposals, and reports from inside Obsidian. It is intended to be copied manually into a vault note, or published through the normal `observe -> proposal -> approval manifest -> apply -> verify` gate. External workers must not write this note directly into a live vault.

## Safety contract

- Status and report material may be generated under repository or build output paths such as `out/`.
- Publishing into `/home/hermesadmin/Obsidian` requires a manual copy by Дмитрий or an approved obslayer proposal/apply run.
- Direct external writes, deletes, moves, and merges in the live vault remain forbidden.
- Dashboard rows are review aids only; they are not approval manifests.

## Status labels

| Status | Meaning | Next action |
| --- | --- | --- |
| `proposed` | Worker produced a proposal, report, or candidate change. | Review evidence and decide whether to approve, reject, or request changes. |
| `needs-review` | Human/agent review is required before any apply. | Check source evidence, risk notes, and affected paths. |
| `applied` | Approved apply completed and verification evidence exists. | Confirm post-verify report and archive/close. |
| `rejected` | Proposal is not accepted or is superseded. | Record reason and do not apply. |

## Expected vault structure and empty-state guidance

This dashboard expects review notes to live under these vault paths after manual copy or approved apply:

| Path | Purpose |
| --- | --- |
| `Hermes/Review` | review queue notes and task checklists |
| `Hermes/Review/Proposals` | proposal review notes generated from `proposal.json` bundles |
| `Hermes/Reports` | final reports, acceptance reports, and delivery summaries |

If a Dataview block is empty, treat it as one of these states:

1. no matching review/report notes have been published into the vault yet;
2. the note is still only in repository/output storage and has not passed the publish gate;
3. tags/status fields are missing or not using the constrained labels above.

An empty block is not approval evidence. Use the CLI dashboard first when in doubt:

```bash
python3 tools/obsidian_review_dashboard.py list --proposal-root out/proposals --json
```


## Semantic proposal-only reports

Semantic query proposal-only reports are review-candidate artifacts, not target-diff proposals. For these reports:

- `targets: []` is expected and means no apply target is authorized.
- The primary review surface is `candidates`, `summary`, `queries`, and `safety`.
- `tools/obsidian_review_dashboard.py explain` must show candidate notes, query intents, chunk references, safety boundary, and next safe step.
- `explain` accepts either `--proposal path/to/proposal.json` or the shorter positional form `explain path/to/proposal.json`; both are read-only.
- Candidate tables must escape Markdown table delimiters from paths, queries, scores, and chunk labels so review output cannot be structurally misleading.
- Approval phrase is not applicable until a later, separate target-diff proposal and explicit approval manifest exists.
- Candidate notes are inputs for review only; they do not authorize live vault mutation.

## Review queue

```dataview
TABLE status, phase, candidate_type, recommended_route, approved_at
FROM "Hermes/Review"
WHERE contains(tags, "obslayer/review") AND status != "applied" AND status != "rejected"
SORT status ASC, approved_at DESC
```

## Proposal index

```dataview
TABLE status, proposal_path, verifier, risk, updated
FROM "Hermes/Review/Proposals"
WHERE contains(tags, "obslayer/proposal")
SORT updated DESC
```

## Report index

```dataview
TABLE status, report_path, verification, delivery_status, updated
FROM "Hermes/Reports"
WHERE contains(tags, "obslayer/report") OR contains(tags, "obslayer/final-report")
SORT updated DESC
```

## Task index

```dataview
TASK
FROM "Hermes/Review"
WHERE contains(tags, "obslayer/task") OR contains(tags, "obslayer/review")
GROUP BY status
```

## Manual review checklist

- [ ] Source item/proposal is linked.
- [ ] Affected paths are listed as absolute paths.
- [ ] Safety boundary says whether this is read-only, proposal-only, or approved apply.
- [ ] Verification command and result are attached.
- [ ] Status is one of `proposed`, `needs-review`, `applied`, or `rejected`.
- [ ] If status is `applied`, post-verify evidence is linked.
