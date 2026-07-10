# Семейство `link-hygiene`

## Зачем

Это proposal-only конвейер разбора broken и ambiguous wikilinks (сломанных и
неоднозначных внутренних ссылок). Он уменьшает шум, но не исправляет заметки
автоматически.

## Инструменты и поток

```text
remaining_link_triage
-> remaining_link_target_discovery
-> lane_schema_v1
-> archive_shadow_index
-> candidate_scorer
-> manual_review_selector or safe_auto_proposal_thresholds
-> manifest_candidate_selector
-> operator review
```

Дополнительные read/baseline-инструменты:
`obsidian_standing_safe_link_prefix_baseline.py` и
`obsidian_standing_safe_link_prefix_policy.py`.

Полные имена CLI: `obsidian_remaining_link_triage.py`,
`obsidian_remaining_link_target_discovery.py`, `obsidian_lane_schema_v1.py`,
`obsidian_archive_shadow_index.py`, `obsidian_candidate_scorer.py`,
`obsidian_manual_review_selector.py`,
`obsidian_safe_auto_proposal_thresholds.py`,
`obsidian_manifest_candidate_selector.py`,
`obsidian_standing_safe_link_prefix_baseline.py` и
`obsidian_standing_safe_link_prefix_policy.py`.

## Границы решений

- Protected, generated, suppressed и ambiguous кандидаты не идут в auto path.
- Archive-shadow и semantic similarity являются слабыми сигналами.
- `safe_auto` означает только безопасно сформированный dry-run proposal, а не
  автоматический live apply.
- Любая будущая правка ссылки проходит общий core-vault workflow.

## Проверка

Тесты: `tests/test_remaining_link_triage.py`,
`tests/test_remaining_link_target_discovery.py`, `tests/test_lane_schema_v1.py`,
`tests/test_archive_shadow_index.py`, `tests/test_candidate_scorer_v1.py`,
`tests/test_manual_review_selector_v1.py`,
`tests/test_safe_auto_proposal_thresholds_v1.py`,
`tests/test_manifest_candidate_selector.py` и
`tests/test_standing_safe_link_prefix_*.py`.

Остановиться при защищённом источнике, нескольких равноценных целях,
недостаточном confidence (уверенности), устаревшем index или отсутствии
операторского review.
