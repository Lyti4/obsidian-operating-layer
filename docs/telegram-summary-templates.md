# Telegram Summary Templates

Short operator-facing templates for reporting Obsidian Operating Layer runs back to Dmitry.

## Rules

- Result first, evidence second.
- Include exact artifact paths because Dmitry cannot inspect server files directly.
- Never include secrets, tokens, cookies, private keys, browser profiles, or raw `.env` values.
- Use the exact phrase `No secrets were included` in summaries when secret hygiene was checked.
- Say explicitly whether the live vault was mutated.
- For live apply, include approval manifest path, backup path, and post-verify result.

## Safe dry-run / proposal-only result

```text
Готово: <short result>.

Безопасность:
- live vault mutated: no
- mode: read-only / proposal-only / dry-run
- protected paths: refused/checked

Evidence:
- proposal/report: <absolute-or-repo-relative-path>
- tests: <command> -> <result>
- git: <commit or clean status>

Next:
- <one safe next step or “ожидаю approval”>
```

## Sandbox benchmark result

```text
Готово: sandbox benchmark прошёл.

Scope:
- source vault: read-only
- sandbox vault: <path>
- live apply: no

Metrics:
- wall_time_ms: <value>
- max_rss_kb: <value>
- scanned/probes/findings: <value>
- cost_model: <value>

Artifacts:
- json: <path>
- markdown/report: <path>

Verification:
- <command> -> <result>
```

## Manual acceptance performed by Hermes on server

```text
Принял сам на сервере: <dashboard/diagram/report>.

Reason:
- Дмитрий не может открыть server-local files напрямую.

Evidence:
- checked files: <paths>
- acceptance status: accepted / accepted-with-notes / needs-fixes
- fixed blockers: <short list>

Verification:
- <command> -> <result>
```

## Live apply request — approval required

```text
Нужен explicit approval перед live apply.

Proposal:
- proposal: <path>
- vault_root: <path>
- targets: <exact target list>

Safety:
- backup_root: _Backups/obsidian-operating-layer
- require_post_verify: true
- protected paths checked: yes

Approval phrase required:
APPROVE OBSIDIAN APPLY
```

Do not run `--apply` unless Dmitry explicitly approves the exact proposal, vault root, and target set.
