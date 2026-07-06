# 41 — Acceptance Bundle Doctor

Status: accepted repo-only safety gate
Date: 2026-07-06
Scope: validate acceptance/evidence bundles before any future approval/apply readiness step

## Purpose

The acceptance bundle doctor is a narrow repo-only gate after indexing/semantic doctors. It verifies that a slice has evidence, required checks, and no hidden live-apply authority before it can be treated as an accepted operator artifact.

It does **not** scan or mutate the live Obsidian vault. It does **not** create approval manifests. It does **not** grant apply authority.

## Contract

Input bundle mode:

```text
obslayer.acceptance-bundle.v1
```

Doctor output mode:

```text
obslayer.acceptance-bundle-doctor.v1
```

Required bundle safety fields:

```yaml
live_mutation_authorized: false
approval_manifest_created: false
apply_authority: none
target_paths: []
findings: []
```

Allowed artifact roots are repo-local only:

- `out/`
- `docs/spec-kit/`
- `docs/acceptance/`
- `src/`
- `tests/`
- `tools/`

Live vault paths are not valid acceptance artifacts.

Acceptance index files under `docs/acceptance/` are valid repo-local evidence artifacts. They are still documentation/evidence only and do not grant apply authority.

## Required checks

Every required check must have status `passed` or `ok`. Failed or missing required checks block acceptance.

Typical required checks:

```text
python -m pytest <slice tests> -q
python -m ruff check <changed python files>
git diff --check
make verify
```

## CLI

```bash
python tools/obsidian_acceptance_bundle_doctor.py   --bundle out/reports/<slice>/acceptance-bundle.json   --repo .   --out-dir out/reports/<slice>/acceptance-bundle-doctor
```

## Acceptance

- report status is `accepted` only when all findings are empty;
- safety section always reports no live mutation, no approval manifest, no apply authority, and no targets;
- missing required artifacts block acceptance;
- artifacts outside allowed repo roots block acceptance;
- required failed checks block acceptance.

## Position in pipeline

```text
indexing manifest doctor
  -> semantic manifest doctor
  -> acceptance bundle doctor
  -> approved apply readiness (only for a separately approved manifest)
```

This keeps acceptance evidence separate from apply readiness and prevents generated reports from silently becoming edit authority.
