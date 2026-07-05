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
- `25-nanobot-graphify-worker.md` — Nanobot-as-Graphify-worker contract: bridge route, `gpt-5.4-mini`, sandbox/read-only, graph-first before embeddings.
- `26-nanobot-standing-worker.md` — Nanobot standing maintenance/communication worker contract for ongoing project support.
- `28-global-headroom-only-llm-channel.md` — global Headroom-only LLM channel policy: explicit proxy/subscription inheritance, Graphify accepted route, Nanobot backend bridge, account cooldown semantics.
- `29-channel-registry.md` — machine-readable карта ролей/маршрутов/прав мутации для Hermes/Codex/Headroom/Nanobot/Graphify.
- `29-semantic-proposal-workflow.md` — proposal-only semantic review pipeline: Graphify/index evidence → reports → decision packets → targeted proposals.
- `30-orchestrator-operating-spec.md` — first-read consolidated operator-facing spec for Hermes-as-orchestrator, Nanobot worker boundaries, Headroom channels, semantic proposal workflow, and current generated artifact pointers.
- `31-operator-flow-and-review-queue.md` — explicit Agentic OS operator flow and evidence-gated review queue state machine for Hermes/Nanobot/proposal artifacts.
- `32-codex-hermes-communication-channel.md` — local Codex ⇄ Hermes task/report protocol with roles, rights, ACKs, and approval boundaries.
- `33-codex-native-runtime.md` — repo-native Codex runner, task/report schemas, and sandbox fallback policy.
- `34-agentic-improvement-loop.md` — continuous Nanobot → Hermes → spec-kit/queue → Codex review/implementation improvement loop for agentic OS work.
- `35-agentic-os-control-plane-map.md` — single operator control-plane map linking orchestrator, review queue, Codex/Hermes channel, runtime, acceptance gates, channel registry, and docs-lag checks.
- `schemas/adapter-metadata.schema.json` — machine-readable schema для adapters.
- `schemas/llm-channel.schema.json` — secret-free LLM channel smoke artifact schema.
- `schemas/queue-task.schema.json` — machine-readable schema для queue tasks.


## Codex native runtime

Codex is made repo-native through `docs/spec-kit/33-codex-native-runtime.md`, `/home/hermesadmin/.codex-hermes/bin/hermes-codex-run`, schema-versioned task/report packets, and explicit separation from Nanobot's architecture scout channel. Nanobot may recommend Codex tasks; Hermes dispatches and accepts them.


## Agentic improvement loop

`docs/spec-kit/34-agentic-improvement-loop.md` is the operating contract for the continuous improvement cycle: Nanobot scouts and recommends, Hermes collects/triages/specs/queues, Codex reviews or implements bounded repo tasks, and Hermes verifies before acceptance. Project-wide Codex sweeps are review-only and become smaller accepted tasks after Hermes triage.

## Agentic OS control plane map

`docs/spec-kit/35-agentic-os-control-plane-map.md` is the canonical cross-link/index surface requested by repeated Nanobot scout reports. It maps the orchestrator spec, review queue, Codex/Hermes communication channel, Codex native runtime, acceptance gates, channel registry, and docs lag audit into one no-live-mutation control plane.
