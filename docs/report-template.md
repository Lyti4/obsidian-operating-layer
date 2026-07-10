# Obsidian Operating Layer Report Template

Date: YYYY-MM-DD
Task: <task id>
Operator/agent: <role>
Data boundary: <repo-relative or sanitized path class>

## Кто

- Владелец решения:
- Исполнитель:
- Handoff target:

## Зачем

- Пользовательский результат:

## Почему

- Evidence и причина решения:

## Summary

- Observation result:
- Proposal result:
- Apply result:
- Verification result:

## External / local patterns adopted

- Read-only first:
- Dry-run by default:
- Proposal-only mutation:
- JSON for automation + Markdown for humans:
- Protected path and approval guardrails:

## Exact commands

```bash
<command 1>
<command 2>
<command 3>
```

## Changed files

- <path>

## Границы

- Live vault/runtime changed: yes/no
- Approval used: <none or exact approved operation ID/path>
- Secrets included: no

## Safety gates checked

- [ ] proposal path is bound in approval manifest
- [ ] manifest vault root matches proposal vault root
- [ ] manifest targets exactly match proposal targets
- [ ] protected paths refused
- [ ] backup root stays under `_Backups/obsidian-operating-layer`
- [ ] dry-run remains default

## Tests

- <test command>

## Влияние на документацию

- `documentation impact`: <updated canonical/active paths or reasoned none>

## Next safe step

- <one actionable step>

## Термины

- <term>: <короткое русское объяснение>
