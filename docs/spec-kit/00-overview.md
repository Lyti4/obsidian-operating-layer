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
Community plugins / MCP / RAG engines
        ↓ read/search/analyze
Worker orchestrator
        ↓ proposal bundle
Obslayer safety core
        ↓ dry-run / approval / backup / verify
Obsidian vault
```
