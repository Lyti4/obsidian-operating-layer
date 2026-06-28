# Obsidian Operating Layer Report Template

Date: YYYY-MM-DD
Task: <task id>
Operator: <profile>
Vault: <absolute vault path>

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
- <path>

## Safety gates checked

- [ ] proposal path is bound in approval manifest
- [ ] manifest vault root matches proposal vault root
- [ ] manifest targets exactly match proposal targets
- [ ] protected paths refused
- [ ] backup root stays under `_Backups/obsidian-operating-layer`
- [ ] dry-run remains default

## Tests

- <test command>
- <test command>

## Next safe step

- <one actionable step>
