# Obsidian Operating Layer — база готовых компонентов

Дата: 2026-06-28
Источник: GitHub API через `gh` + официальный registry community plugins `obsidianmd/obsidian-releases/community-plugins.json`.
Политика: **готовые рабочие куски сначала**, свой код — только как glue/safety layer.

## Вывод

Не строим автономность с нуля. Собираем систему из готовых слоёв:

1. **Наш safety core** остаётся mutation gate: observe → propose → verify → apply, dry-run, manifest, backups.
2. **Готовые Obsidian plugins** используем как UI/локальные функции: Dataview, Templater, Linter, Tasks, Omnisearch, Metadata Menu, Auto Note Mover, Tag Wrangler и т.п.
3. **Готовые MCP/LLM/RAG компоненты** используем как worker/read/search слой: `cyanheads/obsidian-mcp-server`, `rps321321/obsidian-mcp-pro`, `Kwipu`, `obsidian-local-llm-hub`, `swarmvault`, `dory`.
4. Чужие write-инструменты не получают прямую запись в vault: write requests заворачиваются в наш proposal/apply gate.

## Кандидаты GitHub для интеграции

|bucket|repo|stars|license|language|description|
|---|---|---|---|---|---|
|ready_component_candidate|cyanheads/obsidian-mcp-server|608|Apache-2.0|TypeScript|Read, write, search, and surgically edit Obsidian vault notes, tags, and frontmatter via MCP. STDIO or Streamable HTTP.|
|ready_component_candidate|rps321321/obsidian-mcp-pro|24|MIT|TypeScript|The most feature-complete MCP server for Obsidian vaults — 23 tools + 3 resources for search, read, write, tags, link analysis, graph traversal, and canvas. Also ships as an Obsidian plugin (github.com/rps321321/obsidian|
|ready_component_candidate|smith-and-web/obsidian-mcp-server|17|MIT|TypeScript|MCP server for Obsidian vault management - enables Claude and other AI assistants to read, write, search, and organize your notes|
|ready_component_candidate|bettyguo/obsidian_mcp|8|MIT|Python| MCP server + 7 Claude skills for Obsidian vaults — read, search, write, and link notes from Claude / Cursor / ChatGPT. Filesystem-direct, local-first, round-trip safe.|
|ready_component_candidate|swarmclawai/swarmvault|588|MIT|TypeScript|The local-first LLM Wiki: open-source knowledge graph builder, RAG knowledge base, and agent memory store. Built on Andrej Karpathy's pattern. An Obsidian alternative for personal knowledge management, AI second brain, a|
|ready_component_candidate|benmaster82/Kwipu|255|MIT|Python|Ask questions across your Markdown notes using a fully local Graph RAG engine. Built for Obsidian vaults, works with any folder of Markdown files. Extracts entity-relation triples from wikilinks & YAML frontmatter, retri|
|ready_component_candidate|takeshy/obsidian-local-llm-hub|50|MIT|TypeScript|All-in-one local AI hub for Obsidian — LLM chat with vault tools, MCP servers, RAG, workflow automation, encryption, and edit history. Fully private, no cloud required.|
|ready_component_candidate|deeflect/dory|16|MIT|Python|One memory layer for every AI agent. Local-first, markdown source of truth, and CLI/HTTP/MCP native. Your agent forgot who you are. Again. Dory fixes that.|
|ready_component_candidate|noduslabs/infranodus-obsidian-plugin|152|AGPL-3.0|TypeScript|Advanced graph view for Obsidian: text analysis, topic modeling, and AI with InfraNodus AI text analysis tool: https://infranodus.com|


## Кандидаты Obsidian community plugins

|bucket|name|repo|description|
|---|---|---|---|
|core_ready_plugins|Templater|silentvoid13/Templater|Create and use dynamic templates.|
|core_ready_plugins|Dataview|blacksmithgu/obsidian-dataview|Run advanced queries over your vault.|
|core_ready_plugins|Tag Wrangler|pjeby/tag-wrangler|Rename, merge, toggle, and search tags from the tag pane.|
|core_ready_plugins|Various Complements|tadashi-aikawa/obsidian-various-complements-plugin|Complete words similar to auto-completion in an IDE.|
|core_ready_plugins|Tasks|obsidian-tasks-group/obsidian-tasks|Track tasks across your vault. Supports due dates, recurring tasks, done dates, sub-set of checklist items, and filtering. Maintained by Clare Macrae and Ilyas Landikov, created by Martin Schenck.|
|core_ready_plugins|Linter|platers/obsidian-linter|Format and style your notes. Linter can be used to format YAML tags, aliases, arrays, and metadata; footnotes; headings; spacing; math blocks; regular Markdown contents like list, italics, and bold styles; and more with |
|core_ready_plugins|Auto Note Mover|farux/obsidian-auto-note-mover|Automatically move the active notes to their respective folders according to rules you set.|
|core_ready_plugins|Big Calendar|quorafind/Obsidian-Big-Calendar|A big calendar for Obsidian. All events from your daily notes OR tasks used TASKS/DATAVIEW/KANBAN format.|
|core_ready_plugins|Heatmap Calendar|richardsl/heatmap-calendar-obsidian|Activity Year Overview for DataviewJS, Github style – Track Goals, Progress, Habits, Tasks, Exercise, Finances, "Dont Break the Chain" etc.|
|core_ready_plugins|Omnisearch|scambier/obsidian-omnisearch|Intelligent search for your notes, PDFs, and OCR for images.|
|core_ready_plugins|Release Timeline|cakechaser/obsidian-release-timeline|Release timeline rendered based on notes metadata with a Dataview-like syntax.|
|core_ready_plugins|Metadata Menu|mdelobelle/metadatamenu|For data quality enthusiasts and Dataview users: access and manage the metadata of your notes.|
|core_ready_plugins|File Cooker|ivaneye/obsidian-files-cooker|Deal batch notes from search results,current file, or Dataview query string.|
|core_ready_plugins|Better Inline Fields|dsarman/better-inline-fields|Enhance Dataview-style inline fields.|
|core_ready_plugins|Double Colon Conceal|msrch/obsidian-double-colon-conceal|Display double colon (i.e. Dataview inline fields) as a single colon for more natural reading experience.|
|core_ready_plugins|Habit Calendar|hedonihilist/obsidian-habit-calendar|Monthly Habit Calendar for DataviewJS. Render a calendar inside DataviewJS code block, showing your habit status within a month.|
|core_ready_plugins|Meld Build|meld-cp/obsidian-build|Write and execute (sandboxed) JavaScript to render templates, query DataView and create dynamic notes.|
|core_ready_plugins|Time Ruler|j-palindrome/obsidian-time-ruler|A drag-and-drop time ruler combining the best of a task list and a calendar view (integrates with Tasks, Full Calendar, and Dataview).|
|core_ready_plugins|ICS|open-horizon-labs/obsidian-ics|Add events from calendar ics on the web to daily notes on demand. Includes vdir support. Daily Planner, Templater and Dataview friendly.|
|core_ready_plugins|Moviegrabber|superschnizel/Obsidian-Moviegrabber|Grab movie data from public APIs and transform it into notes that can be used with dataview and properties.|
|core_ready_plugins|Run|hananoshikayomaru/obsidian-run|Generate Markdown from dataview query and JavaScript.|
|core_ready_plugins|Desk|davidlandry93/obsidian-desk|A desk to see notes at a glance. Requires Dataview.|
|core_ready_plugins|AI for Templater|tfthacker/obsidian-ai-templater|AI Extension for the Templater plugin with the OpenAI Client Library.|
|core_ready_plugins|Dataview Publisher|udus122/dataview-publisher|Output markdown from your Dataview queries and keep them up to date. You can also publish them.|
|core_ready_plugins|Dataview Serializer|dsebastien/obsidian-dataview-serializer|Serialize Dataview queries to Markdown, and keep the Markdown representation up to date|
|core_ready_plugins|Todoist Context Bridge|wenlzhang/obsidian-todoist-context-bridge|Bridge your note-taking and Todoist task management workflows with contextual connections. Seamlessly integrate with Dataview and Tasks plugins.|
|core_ready_plugins|Dataview Autocompletion|dnlbauer/obsidian-dataview-autocompletion|Adds autocompletion to Dataview metadata fields|
|core_ready_plugins|QueryDash|liufree/obsidian-querydash|Add new views and enhanced features for bases. Inspired by Dataview and bases, this includes search, sorting, and pagination functionalities similar to Notion.|
|core_ready_plugins|DataCards|sophokles187/data-cards|Transform Dataview query results into visually appealing, customizable card layouts.|
|core_ready_plugins|Virtual Content|signynt/virtual-content|Display markdown text (including dataview queries or Bases) at the bottom, top or in the sidebar for all notes which match a specified rule, without modifying them.|
|core_ready_plugins|Dataview to Properties|mara-li/obsidian-dataview-properties|Automagically copy dataview inline field (and their values, even calculated!) into frontmatter properties and keep them sync.|
|core_ready_plugins|Move Cursor On Startup|treadder/move-cursor-on-startup|Move cursor right then left briefly on startup --> first opened note. Makes DataView expressions 'activate' automatically instead of waiting for user interaction.|
|core_ready_plugins|Workout Logger|viscosenpai/obsidian-workout-logger|Log weight training sessions to notes in a Dataview-friendly format. - This plugin has not been manually reviewed by Obsidian staff.|
|core_ready_plugins|Activity Graph|rwyattwalker/obsidian-activity-graph|Render activity heatmaps from Dataview query results. - This plugin has not been manually reviewed by Obsidian staff.|
|core_ready_plugins|Dropdown Vars|majid-khonji/obsidian-dropdown-vars|Dropdowns in Reading and Live Preview; sync to frontmatter or inline Dataview. - This plugin has not been manually reviewed by Obsidian staff.|


## Архитектурная сборка из готовых частей

### Layer 1 — Safety core / уже есть
- `tools/obsidian_observe.py`
- `tools/obsidian_propose.py`
- `tools/obsidian_verify.py`
- `tools/obsidian_apply.py`
- protected paths + exact proposal/manifest/target binding

### Layer 2 — UI / готовые community plugins
- Dataview: запросы и dashboard поверх vault.
- Templater: шаблоны отчётов/proposals/MOC.
- Linter: нормализация markdown/frontmatter.
- Tasks: задачный слой.
- Omnisearch: локальный быстрый поиск.
- Metadata Menu / Tag Wrangler / Auto Note Mover: управление metadata/tags/routing.

### Layer 3 — Worker/MCP bridge / готовые серверы
- `cyanheads/obsidian-mcp-server`: основной MCP кандидат, много звёзд, read/write/search/frontmatter.
- `rps321321/obsidian-mcp-pro`: богатый набор tools: search/read/write/tags/link analysis/graph/canvas.
- `bettyguo/obsidian_mcp`: Python MCP + Claude skills, проще встроить в Python glue.

### Layer 4 — Retrieval/RAG/Graph / готовые движки
- `Kwipu`: Markdown/Obsidian Graph RAG, wikilinks/YAML, hybrid vector+BM25+temporal, Ollama.
- `swarmvault`: local-first LLM wiki/memory/knowledge graph.
- `obsidian-local-llm-hub`: local AI hub, MCP, RAG, workflows, edit history.
- `dory`: local-first markdown memory layer CLI/HTTP/MCP.

## Правило интеграции

```text
External component/plugin -> read/search/analyze/propose only
Our obslayer safety core -> единственный путь live mutation
Live vault writes -> только через approval manifest + backup + verify
```

## Следующие шаги spec kit

1. Описать component adapters: MCP adapter, Plugin registry adapter, RAG adapter, Proposal adapter.
2. Сделать allowlist capabilities: read/search/graph/propose/write-request, где write-request != direct write.
3. Создать `docs/spec-kit/`:
   - `00-overview.md`
   - `01-component-inventory.md`
   - `02-worker-orchestration.md`
   - `03-safety-contract.md`
   - `04-integration-plan.md`
4. Потом уже выбирать 2–3 компонента для реальной установки/песочницы.

## Raw artifacts

- `/home/hermesadmin/work/obsidian-operating-layer/out/research/github-components.json`
- `/home/hermesadmin/work/obsidian-operating-layer/out/research/obsidian-community-plugins-selected.json`
