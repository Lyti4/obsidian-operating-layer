# Role notes

## Observe

- Read-only scan of the vault.
- Report counts, broken links, duplicates, and orphan notes.
- Never write to the vault.

## Propose

- Convert observation data into a dry-run proposal.
- Include a risk class and safety note.
- Never mutate the vault.

## Apply

- Default to dry-run.
- Real apply requires an approval manifest and `--real`.
- Only perform narrow, explicit actions.
- Create backups before real edits.

## Verify

- Compare observation and proposal artifacts.
- Confirm the counts and target vault match.
- Fail fast on drift.
