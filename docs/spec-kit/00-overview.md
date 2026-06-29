# Spec Kit — Obsidian Operating Layer

Цель: собрать автономный Obsidian operating layer **из готовых рабочих компонентов**, оставив наш код safety/glue слоем.

## Принцип

- Не строить с нуля, если есть рабочий plugin/server/library.
- Чужие компоненты могут читать, искать, анализировать, рисовать схемы, рендерить PDF и генерировать proposals.
- Прямая запись в vault запрещена для внешних компонентов.
- Диаграммы/PDF должны собираться из воспроизводимых source-файлов: Mermaid/Excalidraw-style Markdown, D2, Graphviz, PlantUML, Typst/Quarto.
- Единственный live mutation path: наш `tools/obsidian_apply.py` с approval manifest, backup, verify.

## Target pipeline

```text
Community plugins / MCP / RAG engines / diagram renderers
        ↓ read/search/analyze/render
Worker orchestrator
        ↓ proposal bundle / report bundle / diagram sources
Obslayer safety core
        ↓ dry-run / approval / backup / verify
Obsidian vault
```

## Spec kit files

- `01-component-inventory.md` — база найденных готовых компонентов.
- `02-worker-orchestration.md` — worker/queue/capability модель.
- `03-safety-contract.md` — safety contract и adapter contract.
- `04-integration-plan.md` — phased integration plan.
- `05-final-desired-architecture.md` — финальная желательная архитектура для реализации.
- `06-adapter-contracts.md` — contract/schema для внешних компонентов.
- `07-local-queue-schema.md` — локальная durable queue и worker task schema.
- `08-mcp-sandbox-plan.md` — sandbox-план для MCP серверов.
- `09-rag-graph-sandbox-plan.md` — sandbox-план для RAG/graph компонентов.
- `10-diagram-pdf-pipeline.md` — pipeline красивых схем и PDF.
- `11-implementation-roadmap.md` — порядок реализации по фазам.
- `12-full-functional-and-diagram-test-plan.md` — план полного функционального и diagram/PDF тестирования.
- `13-next-improvements-roadmap.md` — следующий roadmap улучшений после MVP baseline.
- `14-operational-acceptance-report.md` — отчёт о закрытии первого operational acceptance pass.
- `15-manual-and-adapter-acceptance.md` — manual dashboard/diagram acceptance checklist and sandbox-only RAG/MCP benchmark contracts.
- `16-sandbox-e2e-evidence.md` — safe post-P3 sandbox/read-only E2E evidence and refusal checks.
- `17-knowledge-indexing-update-plan.md` — knowledge indexing upgrade plan: catalog, FTS5, graph, optional semantic sidecar, read-only adapter.
- `18-external-indexing-spike-plan.md` — real external indexing runtime/spike plan for `DalecB/obsidian-semantic-mcp` under sandbox/read-only constraints.
- `19-document-system-map.md` — current map of docs, evidence, active/stale surfaces, and next indexing-runtime acceptance slice.
- `20-indexing-runtime-acceptance.md` — accepted state of the guarded indexing runtime, evidence, and remaining production-integration blockers.
- `schemas/adapter-metadata.schema.json` — machine-readable schema для adapters.
- `schemas/queue-task.schema.json` — machine-readable schema для queue tasks.
