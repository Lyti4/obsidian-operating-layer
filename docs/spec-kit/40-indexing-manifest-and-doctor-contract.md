# Indexing Manifest and Doctor Contract

## Purpose

This contract makes future Obsidian vault and file indexing runs auditable before any operator depends on the result. It records what a bounded indexing run saw, what it indexed, what it skipped, why protected or generated material was skipped, and which derived artifacts must exist for review.

The contract is repo-only and proposal-only. It does not authorize live vault mutation, live vault scanning, service creation, cron creation, network exposure, embeddings, or apply.

## Manifest Schema

The durable JSON shape is `obsidian-layer.indexing-manifest.v1`:

```json
{
  "mode": "obsidian-layer.indexing-manifest.v1",
  "created_at": "2026-07-06T00:00:00Z",
  "files_seen": ["Notes/A.md"],
  "indexed": ["Notes/A.md"],
  "skipped": ["_Backups/old.md", "out/report.md"],
  "protected_skipped": ["_Backups/old.md"],
  "generated_skipped": ["out/report.md"],
  "broken_links": [{"source": "Notes/A.md", "target": "Missing"}],
  "orphans": ["Notes/Orphan.md"],
  "duplicates": [{"path": "Notes/A copy.md", "duplicate_of": "Notes/A.md"}],
  "artifacts": {"graph_report": "out/reports/run/GRAPH_REPORT.md"},
  "policy": {
    "live_mutation_enabled": false,
    "max_files_per_run": 50,
    "protected_paths": ["_Backups"],
    "generated_paths": ["out"]
  }
}
```

Required invariants:

- `files_seen` equals the union of `indexed` and `skipped`.
- `indexed` and `skipped` are disjoint.
- `protected_skipped` and `generated_skipped` are subsets of `skipped`.
- `protected_skipped` and `generated_skipped` are disjoint.
- `policy.live_mutation_enabled` is false.
- `policy.max_files_per_run` is positive and must not exceed the embedding hard cap of 75 when doctor-gated.

## Doctor Checks

The doctor report is `obsidian-layer.indexing-doctor.v1` and emits checklist-style checks:

- manifest invariants pass;
- protected skips are tracked;
- generated skips are tracked;
- embedding `max_files_per_run <= 75`;
- live mutation is disabled;
- required named artifacts are present.

The doctor may inspect only artifact paths explicitly provided in the manifest and required by the caller. It must not discover, scan, or mutate `/home/hermesadmin/Obsidian`.

## Safety Constraints

- No live mutation.
- No approval manifest creation.
- No backup, apply, move, delete, or write into a live vault.
- No secret, auth, browser profile, or credential reads.
- No cron, service, public posting, deployment, paid action, or network exposure.
- Generated files and protected paths are tracked as skip evidence, not indexed by default.
- Embedding runs remain bounded by the existing hard cap of 75 files per run.

## Acceptance Gates

A slice using this contract is acceptable only when:

- the manifest validates;
- doctor status is `ready-for-operator-review`;
- protected and generated skips are non-lossy and visible in summaries;
- every required artifact exists;
- live mutation remains disabled;
- tests and `git diff --check` pass for the touched files.

## Future Kanban Slices

- Wire indexing runtimes to emit this manifest after sandbox or repo-only runs.
- Add a review dashboard view for doctor checklist results.
- Add adapter-specific skip classifiers for protected roots and generated reports.
- Add optional Graphify artifact pointers after sandbox extraction.
- Add operator-facing acceptance bundles that combine manifest, doctor report, and evidence summaries without exposing live vault paths.
