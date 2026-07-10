# Handoff — текущая точка входа

**Статус:** `active-pointer`

Этот файл не хранит копию текущего runtime, dirty state или очереди задач.
Начинайте новый сеанс так:

1. `AGENTS.md` — полномочия и общие границы.
2. `docs/INSTRUCTION_TREE.md` — какое узкое правило применяется.
3. `.specify/feature.json` — активная Spec Kit feature и её `tasks.md`.
4. `docs/RUNTIME_STATUS.md` — проверяемое текущее состояние сервисов/jobs.
5. `docs/agents/HERMES.md`, `docs/agents/CODEX.md` или
   `docs/agents/NANOBOT.md` — контракт текущей роли.

Перед изменением проверьте реальный repo state:

```bash
git status --short --branch
git log --oneline -5
```

Старые подробности handoff остаются историческим evidence в Git и не должны
использоваться как текущая authority (полномочие).
