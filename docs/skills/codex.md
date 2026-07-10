# Skill Card — codex

## Use when

- Delegating implementation or review to Codex.
- Debugging Codex runtime/channel/account routing for this project.
- Preparing a bounded code_slice task packet.

## Load full Hermes skills

- `codex`
- `codex-delegation-monitoring` when monitoring a delegated run.
- `codex-hermes-auth-switching` only for auth/account work.

## Read first

- `docs/agents/CODEX.md`
- `.specify/feature.json` and the active feature `tasks.md`
- `docs/spec-kit/32-codex-hermes-communication-channel.md`
- `docs/spec-kit/33-codex-native-runtime.md`

## Do not do

- No live vault mutation.
- No secrets/auth/profile reads in prompts or reports.
- No commits/pushes without a current owner publication approval.
- Every changed code/tool/workflow records `documentation impact`.

## If full Hermes skill is unavailable

Do not block on discovery. Use this card plus linked project docs as the task packet, record `skill_unavailable`, and continue only if the scope remains safe.
