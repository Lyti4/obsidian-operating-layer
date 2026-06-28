# Obsidian Operating Layer

Local, read-only-first tooling for observing an Obsidian vault, drafting proposals, applying approved changes with backups, and verifying results.

## Canonical CLI

The canonical implementation is under `tools/`. Root-level `obsidian_*.py` files are thin compatibility wrappers that execute the matching `tools/obsidian_*.py` command, so old operator muscle memory still works without maintaining a second implementation.

## Project layout

- `tools/obsidian_observe.py` — read-only vault observation to JSON.
- `tools/obsidian_propose.py` — turn an observation bundle into a dry-run proposal bundle.
- `tools/obsidian_proposal_worker.py` — normalize component findings into an obslayer dry-run proposal bundle with evidence, risk, and validated targets.
- `tools/obsidian_apply.py` — dry-run by default; live apply only with an explicit approval manifest.
- `tools/obsidian_verify.py` — verify observation/proposal consistency.
- `tools/obsidian_backfill_report.py` — write an operator report into Obsidian Reports.
- `tools/obsidian_review_dashboard.py` — list/explain pending dry-run proposals for human review without vault mutation.
- `tools/obsidian_sandbox.py` — create/reset protected-path-excluding sandbox vault copies under `out/`.
- `tools/obsidian_controlled_autonomy.py` — explicit Phase 08 observe/index/report queue jobs and acceptance reports; no scheduler is installed.
- `tools/obsidian_field_slice.py` — proposal-only field acceptance slice: observe → finding → proposal → verify → dashboard list → decision record.
- `docs/controlled-autonomy.md` — Phase 08 controlled-autonomy operator notes and safety model.
- `docs/obsidian-review-dashboard/` — Dataview/Templater-friendly Phase 7 review dashboard source notes.
- `obsidian_*.py` — compatibility wrappers for the canonical tools.
- `src/obslayer/guardrails.py` — shared guardrails, approval manifest validation, protected path policy, backup policy.
- `src/obslayer/sandbox.py` — sandbox vault copy/reset harness for read-only component evaluation.
- `tests/` — unit/regression tests for dry-run, approval gating, protected paths, CLI wrappers, and report generation.
- `docs/` — operator guide and report template.
- `manifests/` — checked-in manifest examples only; real manifests belong in task-specific working dirs.
- `out/`, `artifacts/`, `obslayer-backups/`, `.hermes-backups/` — local generated artifacts, ignored by git.

## Adopted design patterns

From the Obsidian task context and GitHub scan, this package adopts patterns rather than external code:

- read-only first and proposal-only mutation boundary;
- dry-run by default, explicit apply only;
- Markdown for humans and JSON for automation;
- deterministic local inspection, no LLM in the tool layer;
- strict capability boundary: observe/propose/apply/verify are separate phases;
- ready components run through sandbox copies first; external adapters stay read/search/analyze/propose/render only;
- live apply requires exact `proposal ↔ approval manifest ↔ vault_root ↔ targets` binding;
- protected namespaces are blocked for proposal targets: `.obsidian`, `_Backups`, `_Archive`, `.trash`, Soul-protected paths;
- backups stay under `_Backups/obsidian-operating-layer` and are created before writes.

## Safety rules

- Observation is read-only.
- Apply defaults to dry-run.
- Real edits require an approval manifest file.
- The approval manifest must name the exact proposal file, vault root, and approved target set.
- Manifest targets must exactly match proposal targets; extra/missing targets fail closed.
- No proposal may target protected namespaces.
- No secrets, payments, public posting, production restarts, Gateway/systemd changes, or network exposure.
- Keep live vault mutations narrowly scoped, backed up, and verified.

## Quick start

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip pytest ruff
make verify
make smoke
```

`make smoke` creates a timestamped `out/smoke-*` directory and runs the full safe pipeline against `/home/hermesadmin/Obsidian`: observe → propose → verify → apply dry-run. It does not delete previous artifacts and does not mutate the vault.

Repository hygiene:

- keep source, docs, tests, examples, and project config in git;
- keep generated run output under ignored local directories (`out/`, `artifacts/`, `obslayer-backups/`, `.hermes-backups/`);
- do not commit real approval manifests that name live vault targets unless Dmitry explicitly approves that artifact.

Run an observation against the local vault:

```bash
python3 tools/obsidian_observe.py \
  --vault /home/hermesadmin/Obsidian \
  --out /tmp/obslayer-observe.json
```

Draft a proposal from the observation bundle:

```bash
python3 tools/obsidian_propose.py \
  --observe /tmp/obslayer-observe.json \
  --out-dir /tmp/obslayer-proposal
```

Normalize component findings into a proposal-only mutation request:

```bash
python3 tools/obsidian_proposal_worker.py \
  --findings /tmp/component-findings.json \
  --vault-root /home/hermesadmin/Obsidian \
  --out-dir /tmp/obslayer-proposal
```

The findings JSON may be either a list of finding objects or an object with `source_id` and `findings`. Each finding target must include `path` and `new_text`; protected namespaces are refused before `proposal.json` is written. The generated proposal stays dry-run by default and still needs an approval manifest before live apply.

List pending proposals for review:

```bash
python3 tools/obsidian_review_dashboard.py list \
  --proposal-root out/proposals \
  --json
```

Explain one proposal in human-readable form:

```bash
python3 tools/obsidian_review_dashboard.py explain \
  --proposal out/proposals/example/proposal.json
```

Both review-dashboard commands are read-only: they inspect proposal bundles and write only to an explicit `--out` path if requested.

Run a proposal-only field slice on an approved vault subset or disposable sandbox:

```bash
python3 tools/obsidian_field_slice.py \
  --vault /tmp/approved-vault-subset \
  --out-root out/field-slices/example \
  --task-id example-field-slice \
  --decision pending
```

This creates observation, findings, proposal, verification, pending-proposals list, and decision records. It never runs live apply.

Dry-run an apply:

```bash
python3 tools/obsidian_apply.py \
  --proposal /tmp/obslayer-proposal/proposal.json \
  --out /tmp/obslayer-apply.json
```

Live apply requires an approval manifest and `--apply`:

```json
{
  "approved": true,
  "proposal": "/tmp/obslayer-proposal/proposal.json",
  "approval_phrase": "APPROVE OBSIDIAN APPLY",
  "task_id": "t_example",
  "approver": "Dmitry",
  "reason": "narrow approved edit",
  "vault_root": "/home/hermesadmin/Obsidian",
  "targets": ["/home/hermesadmin/Obsidian/Memory-Vault/Hermes/Example.md"],
  "backup_root": "_Backups/obsidian-operating-layer",
  "dry_run": false,
  "require_post_verify": true
}
```

```bash
python3 tools/obsidian_apply.py \
  --proposal /tmp/obslayer-proposal/proposal.json \
  --approval-manifest /tmp/obslayer-approval.json \
  --apply \
  --out /tmp/obslayer-apply.json
```

Verify after an apply:

```bash
python3 tools/obsidian_verify.py \
  --observe /tmp/obslayer-observe.json \
  --proposal /tmp/obslayer-proposal/proposal.json
```

Write a final operator report:

```bash
python3 tools/obsidian_backfill_report.py \
  --proposal /tmp/obslayer-proposal/proposal.json \
  --reports-dir /home/hermesadmin/Obsidian/Memory-Vault/Hermes/Reports
```
