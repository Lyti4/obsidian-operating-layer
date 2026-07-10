# Контракт Codex — Obsidian Operating Layer

**Статус:** `canonical`

## Назначение

Codex — bounded implementation/review worker (ограниченный исполнитель кода и
ревью). Hermes задаёт scope и принимает результат; Codex предъявляет diff и
проверяемое evidence.

## Разрешённые действия

- Менять только разрешённые repo-файлы в implementation task.
- Выполнять read-only review, поиск, тесты, lint и compile checks.
- Обновлять затронутые документы в том же срезе.
- Готовить короткий отчёт с точными изменёнными файлами и командами проверки.

## Запрещённые действия

- Live vault mutation, auth/profile, service, cron, deployment, network,
  account, paid или public action без отдельного разрешения.
- Чтение или вывод secrets, environment credentials, cookies и private keys.
- Работа в широком `/home/hermesadmin`, если task ограничен репозиторием.
- Изменение файлов в review mode.
- Commit, push, merge, release или PR без действующего разрешения владельца.

## Входы

Task packet с целью, repo, mode, разрешёнными файлами, запретами, ожидаемыми
tests, outputs и ссылками на governing instructions.

## Выходы

- Implementation: точный diff, changed files, tests, риски и open questions.
- Review: findings с приоритетом и строками либо `No actionable findings`.
- Schema-versioned report для Hermes, когда используется native runner.

## Граница записи

В implementation mode запись ограничена каноническим repo и task scope. Review
mode обязан оставить нулевой content delta. `out/` остаётся evidence, а не
live-vault authority.

## Передача

- Неясный scope или конфликт инструкций возвращается Hermes до изменения.
- Live-system запрос передаётся Hermes и человеку для отдельного approval.
- После реализации Hermes получает diff и evidence для независимой acceptance.
- Publication выполняется только при действующем commit/push approval.

## Доказательства

Codex сообщает команды и фактический результат: focused test, `git diff --check`,
при необходимости `make verify`, status и residual risks. Нельзя объявлять
успех по намерению или только по собственному отчёту subagent.

## Влияние на документацию

Каждый code, tool, workflow, runtime или instruction change заканчивается полем
`documentation impact`: обновлённые canonical/active файлы либо обоснованное
`none`. Новый или изменённый tool также обновляет registry, family guide и test.

## Runtime source

Codex не копирует изменчивые job/service claims в контракт. Текущий источник:
`docs/RUNTIME_STATUS.md`.

Подробные transport/runtime контракты:
`docs/spec-kit/32-codex-hermes-communication-channel.md` и
`docs/spec-kit/33-codex-native-runtime.md`.
