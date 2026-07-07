# 50 — Unified Control-Plane Evidence Index

Status: proposed spec-kit slice
Date: 2026-07-07
Owner: Hermes acceptance; Codex implementation/review worker; Nanobot/companion read-only scout
Scope: repo-only canonical index that resolves the current Obsidian Operating Layer control-plane, evidence, generated reports, proposal queues, worker signals, and acceptance gates into one operator-readable and machine-readable surface.

## Why this exists

Companion deep-review of Nanobot scout reports found that the remaining useful signal is not another isolated report. The repeated need is a single stable entry point that tells Hermes, Codex, Nanobot, Ops, and Dmitry:

- what the current accepted control plane is;
- where the latest evidence artifacts live;
- which generated reports are current vs stale/noise;
- what is ready for operator review;
- which blockers prevent action;
- what can be safely dispatched to Codex/Kanban;
- and which surfaces must remain read-only/proposal-only.

Existing documents already cover slices of this:

| Existing surface | Current role |
|---|---|
| `docs/spec-kit/35-agentic-os-control-plane-map.md` | human control-plane map |
| `docs/spec-kit/36-current-evidence-index.md` | curated evidence pointers |
| `docs/spec-kit/38-unified-queue-state-decision-surface-v1.md` | queue/state vocabulary |
| `docs/spec-kit/40-indexing-manifest-and-doctor-contract.md` | indexing manifest/doctor contract |
| `docs/spec-kit/47-unified-operator-review-index.md` | operator-review artifact index implementation |
| `docs/spec-kit/49-manifest-candidate-selector.md` | narrow selector over operator-review evidence |
| `docs/acceptance/index.md` | accepted capability ledger |

This spec defines the next consolidation layer over those surfaces.

## Non-goals and hard boundaries

This slice must not:

- mutate the live Obsidian vault;
- create or imply an approval manifest;
- apply, move, delete, rename, or rewrite vault notes;
- change auth, profiles, services, cron jobs, gateways, or public network exposure;
- read secrets, raw `.env`, browser profiles, private keys, cookies, or token stores;
- treat generated `out/` reports as source-of-truth without distillation into docs;
- reopen accepted historical lanes unless fresh evidence proves regression.

Live-vault access, if ever needed by a downstream slice, remains read-only observation and must be separately scoped.


## 2026-07-07 Nanobot/Hermes review update

This slice incorporates the latest Nanobot scout recommendation from
`out/reports/nanobot-cron-scout/20260707T093200Z/REPORT.md` and the Hermes review
digest at `out/reports/nanobot-hermes-reviewer/20260707T093248Z/REPORT.md`.

The quick win is a single **evidence-to-decision** entrypoint that cross-links:

1. current repo snapshot / gateway snapshot evidence;
2. accepted capability ledger;
3. semantic review/index and manifest artifacts;
4. control-plane map and queue-state docs;
5. current operator decision / blocker / next-action state.

The structural direction is to normalize the repeated workflow:

```text
discover evidence → summarize → classify → gate → expose decision
```

This spec therefore requires the generated index to be both:

- human-readable: `REPORT.md` as the evidence-to-decision landing page;
- machine-readable: `control-plane-index.json` with deterministic join keys,
  source paths, classifications, warnings, and inert safety flags.

## Proposed artifact set

Implementation should add a deterministic repo-local index builder and generated evidence output.

### Source-controlled spec/docs

- `docs/spec-kit/50-unified-control-plane-evidence-index.md` — this spec.
- Optional update to `docs/spec-kit/36-current-evidence-index.md` pointing to the new canonical generated artifact once implemented.
- Optional update to `docs/acceptance/index.md` only after implementation and verification are accepted.

### Tooling

Preferred tool path:

- `tools/obsidian_unified_control_plane_index.py`

Preferred implementation module, if project conventions favor `src/`:

- `src/obslayer/unified_control_plane_index.py`

Generated output directory:

- `out/reports/unified-control-plane-index/<stamp>/`

Generated files:

- `control-plane-index.json`
- `REPORT.md` — human evidence-to-decision landing page

## Input model

The builder should work with repo-local paths only and implement the workflow
`discover evidence → summarize → classify → gate → expose decision`. It may read:

### Canonical docs

- `docs/acceptance/index.md`
- `docs/spec-kit/35-agentic-os-control-plane-map.md`
- `docs/spec-kit/36-current-evidence-index.md`
- `docs/spec-kit/38-unified-queue-state-decision-surface-v1.md`
- `docs/spec-kit/40-indexing-manifest-and-doctor-contract.md`
- `docs/spec-kit/47-unified-operator-review-index.md`
- `docs/spec-kit/49-manifest-candidate-selector.md`
- `docs/triage/kanban-board.md` when present

### Generated evidence candidates

- selected `out/reports/**/REPORT.md`
- selected `out/proposals/**/REPORT.md`
- selected generated JSON artifacts from existing index/selector/operator-review tools
- Nanobot/companion report directories:
  - `out/reports/nanobot-cron-scout/`
  - `out/reports/nanobot-companion-deep-review/`
  - `out/reports/nanobot-hermes-reviewer/`

The builder must tolerate missing generated paths and classify them rather than crashing.

## Output JSON contract

`control-plane-index.json` should use a stable mode string:

```json
{
  "mode": "obslayer.unified-control-plane-index.v1",
  "generated_at": "ISO-8601 UTC timestamp",
  "repo_root": ".",
  "git": {
    "head": "short-or-full-sha",
    "branch": "name",
    "dirty": false,
    "status_short": []
  },
  "safety": {
    "live_mutation_authorized": false,
    "approval_manifest_created": false,
    "approval_manifest_authority": false,
    "apply_authority": "none",
    "target_paths": []
  },
  "canonical_docs": [],
  "evidence_artifacts": [],
  "worker_signals": [],
  "queue_state": {
    "ready_for_operator_review": 0,
    "blocked": 0,
    "stale": 0,
    "noise_or_trash": 0,
    "accepted_or_closed": 0
  },
  "next_actions": [],
  "blockers": [],
  "warnings": []
}
```

### `canonical_docs[]`

Each item:

```json
{
  "path": "docs/spec-kit/35-agentic-os-control-plane-map.md",
  "exists": true,
  "role": "control-plane-map",
  "status_hint": "active|proposed|accepted|unknown",
  "summary": "short deterministic or extracted summary"
}
```

### `evidence_artifacts[]`

Each item:

```json
{
  "path": "out/reports/.../REPORT.md",
  "exists": true,
  "kind": "report|proposal|index|selector|review|unknown",
  "source": "nanobot|companion|codex|hermes|tool|unknown",
  "classification": "ready_for_operator_review|blocked|stale|noise_or_trash|accepted_or_closed|informational",
  "reason": "short factual reason",
  "safe_to_dispatch": false
}
```

### `worker_signals[]`

Worker signal extraction should stay conservative. It should identify, not trust, worker self-reports.

```json
{
  "worker": "nanobot|companion|codex|ops|hermes|unknown",
  "path": "out/reports/.../REPORT.md",
  "signal": "single stable summary",
  "recommended_owner": "Hermes|Codex|Ops|Docs|Nanobot|Dmitry",
  "requires_human_approval": false
}
```

### `next_actions[]`

Next actions should be bounded and dispatchable, for example:

```json
{
  "id": "unified-index.codex.implementation",
  "title": "Implement deterministic unified control-plane index builder",
  "owner": "Codex",
  "stage": "code_slice",
  "allowed_scope": ["repo-only", "generated artifacts under out/"],
  "forbidden_scope": ["live vault mutation", "secrets", "auth/profile/service/cron changes"],
  "blocked_by": [],
  "acceptance": ["JSON validates", "REPORT generated", "tests pass", "git diff checked"]
}
```

## Classification rules

The implementation should start with deterministic heuristics, not LLM judgement.

### Noise/trash

Classify as `noise_or_trash` when the artifact is only about:

- provider quota exceeded;
- OAuth/auth missing for Nanobot/Codex;
- empty dry-run/no-op;
- duplicate report with no new project signal;
- runtime failure without project evidence.

### Blocked

Classify as `blocked` when the artifact states:

- missing required canonical doc or generated JSON input;
- safety flag violation such as live mutation authority, approval manifest created unexpectedly, non-empty target paths, or apply authority not `none`;
- stale old/live evidence mismatch that prevents action;
- required verification failed.

### Ready for operator review

Classify as `ready_for_operator_review` when:

- source artifact exists;
- safety flags are inert;
- it contains concrete proposed candidates, review items, or next actions;
- no blocker is present;
- and the artifact is not already accepted/closed.

### Accepted/closed

Classify as `accepted_or_closed` when the capability is already recorded in `docs/acceptance/index.md` or the current roadmap as closed, accepted, archived, or done.

### Stale

Classify as `stale` when:

- source artifact points to missing files;
- generated evidence predates a newer accepted source-of-truth doc;
- or a proposal was already applied/verified/nooped and should not be dispatched.

## Report contract

`REPORT.md` should be concise and operator-readable:

1. Executive summary.
2. Safety flags.
3. Canonical docs status.
4. Current evidence counts by classification.
5. Worker signal digest, especially Nanobot/companion signals.
6. Next dispatchable Kanban/Codex slice, if any.
7. Blockers and stale/noise counts.
8. Verification commands run.

## CLI contract

Minimum CLI:

```bash
python3 tools/obsidian_unified_control_plane_index.py   --repo .   --out-dir out/reports/unified-control-plane-index/smoke
```

Useful options:

```text
--artifact PATH       include explicit generated evidence artifact; repeatable
--max-reports N       bound auto-discovered reports, default 50
--json-only           write JSON without markdown report
--strict              exit non-zero on blockers or safety violations
```

All output paths must resolve under the repository. The tool must reject symlink/path escapes.

## Test plan

Codex implementation should add focused tests. Expected coverage:

- JSON shape includes inert safety flags.
- Missing optional generated artifacts become warnings, not crashes.
- Safety violations classify as `blocked`.
- quota/OAuth/dry-run reports classify as `noise_or_trash`.
- concrete proposal/review artifacts classify as `ready_for_operator_review`.
- accepted docs/capabilities classify as `accepted_or_closed` when discoverable.
- output paths cannot escape the repo.
- CLI smoke writes both JSON and `REPORT.md`.

Suggested commands:

```bash
python3 tools/obsidian_unified_control_plane_index.py --repo . --out-dir out/reports/unified-control-plane-index/smoke
pytest -q
ruff check .
git diff --check
```

If `ruff` or full `pytest` is too broad for the current repo state, Codex must run the focused new tests and report why the broader gate was not used.

## Kanban decomposition

Create a chain, not one giant opaque task:

```text
obsidian-layer.unified-control-plane-index.spec
  -> obsidian-layer.unified-control-plane-index.codex-review
  -> obsidian-layer.unified-control-plane-index.code-slice
  -> obsidian-layer.unified-control-plane-index.ops-verification
  -> obsidian-layer.unified-control-plane-index.nanobot-review
  -> obsidian-layer.unified-control-plane-index.docs-acceptance
  -> obsidian-layer.unified-control-plane-index.final-report
```

Initial active work after this spec:

- Codex review of this spec for implementation gaps and safety issues.
- Codex implementation of the deterministic builder only after review is accepted by Hermes.

## Acceptance criteria

This slice is accepted only when:

- this spec exists in source control;
- Codex review report exists and was checked by Hermes;
- implementation writes `control-plane-index.json` and `REPORT.md` under `out/`;
- tests/verification pass or blockers are explicitly recorded;
- generated index classifies current Nanobot/companion reports without live mutation;
- Kanban card chain records evidence and current next stage;
- `docs/acceptance/index.md` is updated only after implementation verification, not at spec-only stage.

## Current next safe step

Dispatch a review-only Codex task against this spec and adjacent docs. Codex must not edit files in review mode. Hermes will use the review to decide the exact implementation packet.


## Blocking review resolutions for implementation

Codex review `t_2de21388` identified three must-fix blockers before code
implementation. The builder contract below resolves them explicitly.

### 1. Bounded evidence discovery over large `out/` trees

The implementation must not recursively ingest the whole `out/` tree by default.
It must use a bounded, deterministic discovery policy:

- start from a curated source list in docs/spec references and known report roots;
- prefer the latest timestamped child per known family unless a CLI flag asks for
  a wider scan;
- default maximums:
  - at most 200 candidate files inspected;
  - at most 50 report families summarized;
  - at most 2 MiB read per individual markdown/json file;
  - skip binary, cache, hidden, secret-like, and oversized paths;
- record all skipped/omitted families as warnings, not crashes;
- provide an explicit `--include-out-glob`/future equivalent only for operator
  selected expansion.

Default mode is therefore a canonical navigation/index pass, not a full archive
crawler.

### 2. Historical accepted live-apply evidence is not an active blocker

The index must distinguish historical evidence from current authorization.
Historical reports may mention live apply, backups, or post-apply verification,
but if they are already recorded in `docs/acceptance/index.md` or another
accepted/closed ledger, they must classify as `accepted_or_closed_evidence`, not
as an active `blocked` state.

Active safety blockers are only current unresolved items with one of these
signals:

- explicit current task/card status `blocked`;
- current report verdict `blocker` or equivalent unresolved gate;
- missing required safety field in the current generated index bundle;
- path/auth/service/live-vault action requested outside allowed scope.

The generated JSON must include both:

- `classification`: e.g. `ready_for_operator_review`, `accepted_or_closed_evidence`,
  `noise_or_trash`, `blocked`, `missing_optional`;
- `authority_state`: always explicit, e.g. `none`, `proposal_only`,
  `historical_accepted`, `requires_explicit_approval`.

### 3. Deterministic join key for accepted/closed classification

Every indexed item must include a stable join key so accepted/closed docs can be
matched to generated artifacts without relying on fuzzy title matching.

Required join key fields:

```json
{
  "stable_key": "obslayer.<family>.<slice>",
  "source_path": "docs/spec-kit/... or out/reports/.../REPORT.md",
  "artifact_family": "unified-control-plane-index",
  "artifact_stamp": "20260707T093200Z or null",
  "canonical_doc": "docs/spec-kit/50-unified-control-plane-evidence-index.md or null"
}
```

Join-key derivation order:

1. explicit `stable_key` in a task/card/report if present;
2. known docs/spec-kit filename mapped to `obslayer.spec.<number-or-slug>`;
3. known `out/reports/<family>/<stamp>/REPORT.md` mapped to
   `obslayer.report.<family>.<stamp>`;
4. fallback SHA-256 of repo-relative path only, prefixed with `obslayer.path.`.

The acceptance ledger and board comments should use the same stable key when
promoting this slice from proposed to accepted.

