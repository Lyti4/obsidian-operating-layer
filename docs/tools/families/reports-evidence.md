# Семейство `reports-evidence`

## Зачем

Семейство создаёт и проверяет отчёты, acceptance bundles, diagrams, benchmarks
и channel evidence. Report (отчёт) объясняет результат, но не является
разрешением на live-изменение.

## Инструменты

- `obsidian_acceptance_bundle_doctor.py` — completeness и safety bundle.
- `obsidian_channel_registry_verify.py` — форма и policy каналов.
- `obsidian_diagram_pdf_report.py` — diagram/PDF artifacts.
- `obsidian_external_tool_benchmark.py` — сравнение внешних сигналов.
- `obsidian_llm_channel_smoke.py` — smoke каналов; live probes только явно.
- `obsidian_project_docs_lag_audit.py` — структурная проверка docs, tool registry и ссылок инструкций.
- `obsidian_backfill_report.py` — запись итогового отчёта в Obsidian Reports.

## Границы

- По умолчанию outputs находятся под выбранным repo-local `out/`.
- Reports не содержат tokens, credentials, private URLs или полные тела заметок.
- PDF/diagram renderer и benchmark не получают live-write authority.
- Live LLM probe требует отдельного разрешения и проверки возможной стоимости.
- `obsidian_backfill_report.py` — исключение с записью в vault; запускать только
  по `docs/runbooks/obsidian_backfill_report.md`.

## Проверка

Тесты: `tests/test_acceptance_bundle_doctor.py`,
`tests/test_channel_registry.py`, `tests/test_diagram_pdf_adapter.py`,
`tests/test_external_tool_benchmark.py`, `tests/test_llm_channel_smoke.py`,
`tests/test_project_docs_lag_audit.py` и `tests/test_backfill_report.py`.

Остановиться при неполном bundle, unsafe flag, неизвестном channel, secret-shaped
выводе, неявном сетевом вызове или попытке представить generated report как
каноническое решение.
