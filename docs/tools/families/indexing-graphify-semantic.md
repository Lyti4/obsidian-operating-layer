# Семейство `indexing-graphify-semantic`

## Зачем

Семейство строит производные индексы, графы, embeddings (числовые представления
смысла) и semantic evidence, не получая права редактировать live vault.

## Инструменты по этапам

- Подготовка и ресурсы: `obsidian_resource_preflight.py`,
  `obsidian_swap_drain.py`.
- Внешние sandbox-indexers: `obsidian_indexing_spike.py`,
  `obsidian_indexing_runtime.py`, `obsidian_indexing_stdio_probe.py`,
  `obsidian_mcp_adapter.py`, `obsidian_rag_graph_adapter.py`.
- Graphify и embeddings: `obsidian_graphify_embedding_handoff.py`,
  `obsidian_graphify_embedding_run.py`, `obsidian_graphify_embedding_query.py`,
  `obsidian_graphify_incremental_index.py`.
- Semantic proposal chain: `obsidian_semantic_proposal_report.py`,
  `obsidian_semantic_candidate_decision_packet.py`,
  `obsidian_semantic_targeted_proposal.py`,
  `obsidian_semantic_review_index.py`, `obsidian_semantic_manifest.py`.
- Doctors (диагностические проверки): `obsidian_indexing_doctor.py` и
  `obsidian_semantic_manifest_doctor.py`.

## Границы

- Graph-first: сначала строится и проверяется граф, затем при необходимости
  embeddings. Сходство — evidence, а не основание для автоматической правки.
- Indexers, MCP и RAG работают с sandbox-копией и derived-root (каталогом
  производных данных), а не с live vault.
- Proposal-chain пишет только под выбранные `out/reports` или `out/proposals`.
- Внешний provider и live LLM probe требуют отдельного разрешения, контроля
  стоимости и очистки отчёта от секретов.
- `obsidian_swap_drain.py` меняет состояние хоста и запускается только по
  `docs/runbooks/obsidian_swap_drain.md`.

## Порядок

```text
resource preflight -> sandbox -> graph/index -> bounded query
-> semantic proposal -> human review -> manifest doctor
```

Ни один результат этой цепочки не передаётся прямо в `obsidian_apply.py` без
обычного proposal, review, approval manifest, backup и verify.

## Проверка и остановка

Тестовые поверхности: `tests/test_indexing_*`, `tests/test_mcp_adapter.py`,
`tests/test_rag_graph_adapter.py`, `tests/test_graphify_*`,
`tests/test_semantic_*` и `tests/test_resource_preflight.py`.

Остановиться при выходе пути из sandbox/`out/`, нехватке RAM, активной тяжёлой
нагрузке, неожиданном сетевом вызове, превышении лимита файлов, неполном
manifest или попытке получить live-write authority.
