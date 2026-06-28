# Obsidian Operating Layer

Local, read-only-first tooling for observing an Obsidian vault, drafting proposals, applying approved changes with backups, and verifying results.

## Canonical CLI

The canonical implementation is under `tools/`. Root-level `obsidian_*.py` files are thin compatibility wrappers that execute the matching `tools/obsidian_*.py` command, so old operator muscle memory still works without maintaining a second implementation.

## Project layout

- `tools/obsidian_observe.py` — read-only vault observation to JSON.
- `tools/obsidian_propose.py` — turn an observation bundle into a dry-run proposal bundle.
- `tools/obsidian_apply.py` — dry-run by default; live apply only with an explicit approval manifest.
- `tools/obsidian_verify.py` — verify observation/proposal consistency.
- `tools/obsidian_backfill_report.py` — write an operator report into Obsidian Reports.
- `obsidian_*.py` — compatibility wrappers for the canonical tools.
- `src/obslayer/guardrails.py` — shared guardrails, approval manifest validation, protected path policy, backup policy.
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
python3 -m pytest -q
python3 -m ruff check .
```

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
