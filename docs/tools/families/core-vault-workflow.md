# Семейство `core-vault-workflow`

## Зачем

Это основной безопасный путь от наблюдения до возможного изменения Obsidian:

```text
observe -> propose -> review -> explicit approval -> backup -> apply -> verify
```

## Инструменты

| Инструмент | Роль | Режим |
|---|---|---|
| `obsidian_observe.py` | Снять read-only observation | `proposal-only` |
| `obsidian_propose.py` | Подготовить dry-run proposal | `proposal-only` |
| `obsidian_proposal_worker.py` | Нормализовать внешние findings | `proposal-only` |
| `obsidian_field_slice.py` | Выполнить полный acceptance-срез без apply | `proposal-only` |
| `obsidian_approved_apply_readiness.py` | Связать proposal и approval manifest | `proposal-only` |
| `obsidian_apply.py` | Сделать одобренную запись с backup | `approved-write` |
| `obsidian_verify.py` | Проверить согласованность artifacts | `read-only` |
| `obsidian_sandbox.py` | Создать изолированную копию vault | `sandbox` |

## Полномочия и данные

- Hermes владеет acceptance (приёмкой результата), человек — явным approval
  (разрешением), Codex и Nanobot могут только готовить или проверять evidence.
- Observation и proposal пишутся в выбранный `out/`-каталог.
- Sandbox не содержит защищённые пути и не становится источником live-истины.
- `obsidian_apply.py` — единственная строка этого семейства с правом live write.
  Для неё обязателен `docs/runbooks/approved-live-apply.md`.
- `.obsidian`, `_Backups`, `_Archive`, `.trash` и Soul-защищённые пути не являются
  целями apply.

## Безопасный запуск

Для анализа без изменения vault используйте
`docs/runbooks/observe-propose-verify.md`. Перед approved apply сверяйте точные
пути, hashes (контрольные хеши), backup root и число файлов.

## Проверка и остановка

Основные тесты: `tests/test_obsidian_operating_layer.py`,
`tests/test_proposal_normalization.py`, `tests/test_field_slice.py`,
`tests/test_approved_apply_readiness_v1.py`, `tests/test_apply_rehearsal.py` и
`tests/test_sandbox_harness.py`.

Остановиться при несовпадении manifest и proposal, изменившемся base hash,
защищённой цели, ошибке backup или post-verify. Proposal и report сами по себе
не являются разрешением на apply.
