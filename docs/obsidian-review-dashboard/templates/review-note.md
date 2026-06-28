---
title: "<% tp.file.title %>"
phase: 7
status: needs-review
candidate_type: docs
recommended_route: docs
proposal_path: ""
report_path: ""
verifier: ""
risk: "unknown"
updated: "<% tp.date.now('YYYY-MM-DD') %>"
tags:
  - obslayer/review
  - obslayer/task
write_policy: proposal_only
---

<%*
const statusOptions = ["proposed", "needs-review", "applied", "rejected"];
tR += `<!-- valid status values: ${statusOptions.join(", ")} -->`;
%>

# <% tp.file.title %>

## Summary

- Item/task: 
- Candidate type: docs
- Recommended route: docs
- Current status: `needs-review`
- Safety boundary: proposal/report surface only; no direct live Obsidian write.

## Source evidence

| Field | Value |
| --- | --- |
| Item file |  |
| Proposal path |  |
| Report path |  |
| Verification command |  |
| Verification result |  |

## Review decision

Choose exactly one status label before moving this note forward:

- `proposed` — proposal/report exists but is not accepted yet.
- `needs-review` — reviewer input is required before apply or publication.
- `applied` — approved apply completed and post-verify evidence is linked.
- `rejected` — proposal should not be applied; record the reason below.

Decision:

Reason:

Reviewer:

Date:

## Safety checklist

- [ ] This note was created manually in Obsidian or generated under a safe output directory first.
- [ ] No external worker wrote directly into the live vault.
- [ ] Any live publication has an approval manifest or explicit manual action.
- [ ] Proposal targets avoid protected namespaces: `.obsidian`, `_Backups`, `_Archive`, `.trash`, Soul-protected paths, secrets, and credentials.
- [ ] Verification evidence is linked before marking `applied`.

## Linked outputs

```dataview
TABLE status, proposal_path, report_path, verifier, updated
FROM "Hermes/Review"
WHERE file.name = this.file.name OR contains(file.outlinks, this.file.link)
SORT updated DESC
```
