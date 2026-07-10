# Runbook — `hermes_codex_run.py`

## Назначение

Runner запускает Codex в каноническом репозитории. В `implementation` mode он
может изменить исходники и документацию, поэтому это approved-write
(утверждённая запись), даже если внутренний Codex sandbox называется
`workspace-write`.

## До запуска

1. Проверить точный repo, ветку и `git status --short --branch`.
2. Отделить уже существующие изменения пользователя от задачи runner.
3. Task packet должен содержать цель, разрешённые файлы, запреты, tests,
   outputs и `documentation impact`.
4. Для `review` mode ожидать нулевой diff; для `implementation` mode заранее
   определить допустимый diff и rollback path.
5. Live vault, auth, services, cron, deployment, network и secrets не входят в
   repo-разрешение.

## Запуск

Implementation:

```bash
python3 tools/hermes_codex_run.py \
  --repo /home/hermesadmin/work/obsidian-operating-layer \
  --mode implementation \
  --task /absolute/path/to/codex_task.v1.json
```

Review-only:

```bash
python3 tools/hermes_codex_run.py \
  --repo /home/hermesadmin/work/obsidian-operating-layer \
  --mode review \
  --task /absolute/path/to/codex_task.v1.json
```

`danger-full-access` не включается автоматически. Он требует отдельного
решения, записанной причины и обоих флагов runner.

## Проверка

- Runner создал schema-valid `codex_report.v1` и sanitized log.
- Review mode не изменил ни tracked, ни untracked content.
- Implementation mode перечислил каждый изменённый файл.
- Hermes отдельно просмотрел diff и запустил указанные tests; для кода обычно
  обязательны `git diff --check` и `make verify`.
- Commit/push выполняются только при действующем разрешении владельца проекта.

## Откат

- Не использовать `git reset --hard` и не удалять чужие изменения.
- Для ошибочного незакоммиченного diff остановиться, сохранить evidence и
  запросить разрешение на точечное восстановление только файлов задачи.
- Для уже опубликованного коммита подготовить отдельный revert commit
  (обратный коммит), проверить его и отправить только с разрешением публикации.
- После отката повторить tests и убедиться, что исходные пользовательские
  изменения сохранены.

## Стоп-условия

Неизвестный dirty state, задача вне канонического repo, недостаточный scope,
secret в packet/log, изменение в review mode, неожиданный live-system запрос,
неполный отчёт или failed verification.
