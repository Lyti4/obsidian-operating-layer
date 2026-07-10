# Семейство `operator-control-plane`

## Зачем

Это пульт Hermes и человека: он сводит очередь, evidence, решения, blockers и
следующее безопасное действие. Его artifacts инертны — они описывают состояние,
но не дают права менять vault, сервис или репозиторий.

## Инструменты

- `obsidian_controlled_autonomy.py` — ручные queue jobs без права включать cron.
- `obsidian_operator_decision_ledger.py` — append-only журнал слабого evidence.
- `obsidian_operator_review_packet.py` — короткий пакет для решения.
- `obsidian_operator_review_queue.py` — текущая очередь review.
- `obsidian_candidate_volume_operator_packet.py` — объёмы и route buckets.
- `obsidian_review_dashboard.py` — просмотр и проверка dashboard source.
- `obsidian_unified_operator_review_index.py` — единый review index.
- `obsidian_unified_control_plane_index.py` — docs, evidence, workers и next action.

## Владение и границы

- Hermes проверяет свежесть и принимает результат; человек утверждает опасные
  действия. Codex и Nanobot могут предложить новый queue item, но не принять его.
- `out/` — evidence, не источник окончательной истины.
- Ledger не заменяет approval manifest и не должен хранить секреты или полные
  тексты заметок.
- Controlled autonomy не включает scheduler (планировщик), service или cron.

## Проверка

Используйте одноимённые тесты `tests/test_operator_*`,
`tests/test_candidate_volume_operator_packet.py`,
`tests/test_review_dashboard*.py`, `tests/test_controlled_autonomy.py`,
`tests/test_unified_operator_review_index.py` и
`tests/test_unified_control_plane_index.py`.

Остановиться при stale evidence, неизвестном artifact schema, расхождении
канонических документов, попытке dispatch без полномочий или выдаче proposal за
принятое решение.
