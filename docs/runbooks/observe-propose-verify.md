# Runbook — Observe, Propose, Verify

Use this for safe live-vault analysis without mutation.

## Preconditions

- Work from project root: `/home/hermesadmin/work/obsidian-operating-layer`.
- Do not edit the live vault manually during the run.
- Keep outputs under `out/`.

## Commands

```bash
make verify
python3 tools/obsidian_observe.py --vault /home/hermesadmin/Obsidian --out out/observe
python3 tools/obsidian_propose.py --observation out/observe/observation.json --out out/propose
python3 tools/obsidian_verify.py --vault /home/hermesadmin/Obsidian --baseline out/observe/observation.json --current out/observe/observation.json --out out/verify
```

## Expected result

- Observation and proposal artifacts are created under `out/`.
- No live vault files are changed.
- Verify reports no unexpected drift.

## Stop conditions

- Any command fails.
- A proposed target is under a protected path.
- A report contains secrets or raw credentials.
