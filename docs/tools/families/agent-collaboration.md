# Семейство `agent-collaboration`

## Зачем

Семейство передаёт ограниченные задачи и evidence между Hermes, Codex и
Nanobot. Hermes остаётся orchestrator (координатором) и acceptance owner
(владельцем приёмки).

## Инструменты

| Инструмент | Назначение | Граница |
|---|---|---|
| `codex_hermes_comm.py` | Task, report и ACK packets | Только `~/.codex-hermes/comm` |
| `hermes_codex_run.py` | Approved-write запуск Codex с policy snapshot | Канонический repo по отдельному runbook |
| `nanobot_readonly_evidence_gateway.py` | Локальный evidence gateway | GET/HEAD/OPTIONS и allowlist |
| `nanobot_review_packet.py` | Компактный пакет для review | Выбранный repo-local output |

## Права ролей

- Hermes формирует scope, проверяет результат и общается с пользователем.
- Codex может менять только разрешённый repo в implementation mode; review mode
  обязан завершаться без diff.
- Nanobot наблюдает весь проект по архитектуре, документации, тестам, очередям,
  runtime evidence, рискам и улучшениям, но только read-only/proposal-only.
- Ни один worker не получает live vault, auth, service, cron, deployment,
  external paid API или public-posting права из сообщения другого агента.

## Безопасность

- Packet содержит ID, scope, ограничения, ожидаемые outputs и verification.
- Секретные переменные среды удаляются, вывод очищается, пути проверяются.
- `danger-full-access` требует отдельного операторского решения и не является
  значением по умолчанию.
- Implementation-запуск `hermes_codex_run.py` может менять канонический repo и
  поэтому выполняется только по `docs/runbooks/hermes_codex_run.md`; название
  sandbox не превращает канонический repo в копию или derived data.
- Gateway слушает только локальную поверхность и не открывается наружу без
  отдельного сетевого решения.

## Проверка

Тесты: `tests/test_codex_hermes_comm.py` и
`tests/test_nanobot_readonly_evidence_gateway.py`. Связанные спецификации:
`docs/spec-kit/25-nanobot-graphify-worker.md`,
`docs/spec-kit/26-nanobot-standing-worker.md`,
`docs/spec-kit/32-codex-hermes-communication-channel.md` и
`docs/spec-kit/33-codex-native-runtime.md`.
