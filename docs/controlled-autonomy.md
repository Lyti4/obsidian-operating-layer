# Controlled Autonomy

**Статус:** `active-contract`. Это описание ручной queue-модели, а не утверждение
о текущем scheduler. Runtime всегда проверяется в `docs/RUNTIME_STATUS.md`.

Phase 08 adds a local, explicit controlled-autonomy slice for scheduled-intent observe/index/report work. It records jobs in `out/queue/`, but it does not install cron, systemd units, gateway jobs, or any production scheduler.

Включение или возобновление реального scheduler остаётся отдельным runtime
изменением с approval и rollback; Nanobot role сам его не включает.

## Safety model

- Supported job kinds are only `observe`, `index`, and `report`.
- Jobs are `read-only-live` by default and record `direct_write_enabled: false`.
- Any write-like result remains `proposal_only` and still requires the existing `obsidian_apply.py` approval manifest contract before live apply.
- Rollback evidence is reported from approved apply results when provided; controlled autonomy never performs rollback or live mutation automatically.
- Stale `running` jobs are cleaned up by moving them to `failed` with an audit note, not by deleting evidence.

## Manual dry-run usage

Create and run an index job:

```bash
python3 tools/obsidian_controlled_autonomy.py --queue-root out/queue create \
  --kind index \
  --vault /home/hermesadmin/Obsidian \
  --task-id phase08-index

python3 tools/obsidian_controlled_autonomy.py --queue-root out/queue run \
  --task-id phase08-index
```

List tracked jobs:

```bash
python3 tools/obsidian_controlled_autonomy.py --queue-root out/queue list
```

Clean up stale running records without deleting audit evidence:

```bash
python3 tools/obsidian_controlled_autonomy.py --queue-root out/queue cleanup \
  --older-than-seconds 3600
```

Write an acceptance report that distinguishes proposed, dry-run, and applied work:

```bash
python3 tools/obsidian_controlled_autonomy.py --queue-root out/queue report \
  --out out/reports/controlled-autonomy-acceptance.md \
  --json-out out/reports/controlled-autonomy-acceptance.json \
  --apply-result /path/to/obsidian-apply-result.json
```

The `--apply-result` argument is optional. If no approved live apply result is attached, the report states that no rollback backup was created by controlled autonomy.
