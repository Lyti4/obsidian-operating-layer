# Skill Card — nanobot

## Use when

- Asking Nanobot for read-only/proposal-only review.
- Reviewing scout reports or communication handoffs.
- Checking Nanobot availability for OOL evidence review.

## Load full Hermes skill

`nanobot`

## Read first

- `docs/agents/NANOBOT.md`
- `docs/spec-kit/26-nanobot-standing-worker.md`
- `docs/spec-kit/30-orchestrator-operating-spec.md`

## Do not do

- Nanobot does not directly accept, close, or apply recommendations.
- No live vault/repo mutation unless separately scoped and approved.
- No secrets/auth/env/cookie/private-key access.

## If full Hermes skill is unavailable

Do not block on discovery. Use this card plus linked project docs as the task packet, record `skill_unavailable`, and continue only if the scope remains safe.
