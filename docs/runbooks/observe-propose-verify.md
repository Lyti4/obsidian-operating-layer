# Runbook — Observe, Propose, Verify

Use this for safe live-vault analysis without mutation.

## Preconditions

- Work from project root: `/home/hermesadmin/work/obsidian-operating-layer`.
- Do not edit the live vault manually during the run.
- Keep outputs under `out/`.

## Commands

```bash
make verify
make live-proposal-only
```

Manual equivalent:

```bash
stamp=$(date -u +%Y%m%dT%H%M%SZ)
base="out/live-proposal-only-$stamp"
mkdir -p "$base"
python3 tools/obsidian_observe.py --vault /home/hermesadmin/Obsidian --out "$base/observation.json"
python3 tools/obsidian_propose.py --observe "$base/observation.json" --out-dir "$base/propose"
python3 tools/obsidian_verify.py --observe "$base/observation.json" --proposal "$base/propose/proposal.json" --json-only > "$base/verify.json"
```

## Expected result

Machine-readable success is `verify.json` with `ok: true` and an empty `issues` list.

- Observation and proposal artifacts are created under `out/`.
- No live vault files are changed.
- Verify reports no unexpected drift.

## Stop conditions

- Any command fails.
- A proposed target is under a protected path.
- A report contains secrets or raw credentials.
