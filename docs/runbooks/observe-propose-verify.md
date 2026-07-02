# Runbook — Observe, Propose, Verify

Use this for safe live-vault analysis without mutation.

## Preconditions

- Work from project root: `/home/hermesadmin/work/obsidian-operating-layer`.
- Do not edit the live vault manually during the run.
- Keep outputs under `out/`.

## Commands

```bash
make verify
stamp=$(date -u +%Y%m%dT%H%M%SZ)
base="out/live-proposal-only-$stamp"
mkdir -p "$base"
python3 tools/obsidian_observe.py --vault /home/hermesadmin/Obsidian --out "$base/observation.json"
python3 tools/obsidian_propose.py --observe "$base/observation.json" --out-dir "$base/propose"
python3 tools/obsidian_verify.py --observe "$base/observation.json" --proposal "$base/propose/proposal.json" | tee "$base/verify.txt"
```

## Expected result

Note: `obsidian_verify.py` currently prints a human status line followed by JSON. Treat `verification ok` and an empty `issues` list as success.


- Observation and proposal artifacts are created under `out/`.
- No live vault files are changed.
- Verify reports no unexpected drift.

## Stop conditions

- Any command fails.
- A proposed target is under a protected path.
- A report contains secrets or raw credentials.
