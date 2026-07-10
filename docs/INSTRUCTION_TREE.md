# Дерево инструкций Obsidian Operating Layer

**Статус:** `canonical`

**Назначение:** показать, какое правило действует, где лежит текущая истина и
как изменение оставляет проверяемый след в документации.

## Порядок полномочий

1. Системные, developer и явные пользовательские инструкции находятся вне
   репозитория и имеют высший приоритет.
2. Корневой `AGENTS.md` задаёт проектные границы.
3. Ближайший к изменяемому файлу вложенный `AGENTS.md` уточняет правила только
   для своего каталога.
4. Контракт роли под `docs/agents/` ограничивает действия Hermes, Codex или
   Nanobot.
5. `docs/tools/INDEX.md` и семейная инструкция объясняют контракт инструмента.
6. Runbook (пошаговая инструкция) описывает конкретную рискованную операцию.
7. Spec Kit (набор связанных спецификаций и задач), старые планы, аудиты и
   отчёты не расширяют разрешения сами по себе.

Узкая инструкция наследует родительские правила и **must not weaken**
(не может ослабить) безопасность, границы данных, необходимость утверждения или
запрет на раскрытие секретов. При неустранимом конфликте работа останавливается
до решения владельца.

## Быстрая навигация

`links_from_root` — максимальное число документальных переходов от корневого
`AGENTS.md` до узкого правила или его канонического продолжения.

<!-- navigation-table:start -->
| area | nearest_instruction | canonical_follow_up | links_from_root |
|---|---|---|---|
| `/` | `AGENTS.md` | `docs/INSTRUCTION_TREE.md` | 1 |
| `docs/` | `docs/AGENTS.md` | `docs/RUNTIME_STATUS.md` | 2 |
| `docs/agents/` | `docs/agents/AGENTS.md` | `docs/agents/HERMES.md` | 3 |
| `tools/` | `tools/AGENTS.md` | `docs/tools/INDEX.md` | 3 |
| `src/obslayer/` | `src/obslayer/AGENTS.md` | `docs/TOOLS_POLICY.md` | 3 |
| `tests/` | `tests/AGENTS.md` | `specs/001-instruction-tree-tool-documentation/quickstart.md` | 3 |
<!-- navigation-table:end -->

## Канонические владельцы тем

| Тема | Канонический источник | Что там хранится |
|---|---|---|
| Проектные полномочия | `AGENTS.md` | общие разрешения, запреты и проверка |
| Дерево инструкций | `docs/INSTRUCTION_TREE.md` | приоритет, области и классификация |
| Цель и состояние проекта | `docs/PROJECT_OVERVIEW.md` | понятная текущая картина |
| Карта файлов и доказательств | `docs/PROJECT_MAP.md` | навигация по репозиторию |
| Архитектура | `docs/ARCHITECTURE.md` | компоненты и потоки управления |
| Долговечные решения | `docs/DECISIONS.md` | принятые решения и причины |
| Политика инструментов | `docs/TOOLS_POLICY.md` | режимы чтения, proposal, sandbox и apply |
| Навыки | `docs/PROJECT_SKILLS.md` | маршрутизация skill (повторяемого рабочего процесса) |
| Текущий runtime | `docs/RUNTIME_STATUS.md` | проверяемое состояние сервисов и заданий |
| Безопасность | `SECURITY.md` | сообщение об уязвимостях и границы данных |
| Контракты ролей | `docs/agents/AGENTS.md` | общая форма Hermes, Codex и Nanobot |
| Реестр инструментов | `docs/tools/INDEX.md` | один ряд на каждый `tools/*.py` |
| Планирование функций | `.specify/memory/constitution.md` | обязательные принципы Spec Kit |
| Активная функция | `.specify/feature.json` | путь к текущему каталогу под `specs/` |

## Активные рабочие инструкции

Следующие файлы имеют статус `active` и должны ссылаться на канонического
владельца темы:

- `README.md` и `HANDOFF.md` — точки входа, не отдельные источники полномочий;
- `docs/operator-guide.md`, `docs/controlled-autonomy.md`,
  `docs/release-readiness.md`, `docs/orchestration-board.md`;
- `docs/component-inventory.md`;
- `docs/github-integration.md`, `docs/github-integration-rollout.md`,
  `docs/github-marketplace-integrations.md`;
- `docs/agents/HERMES.md`, `docs/agents/CODEX.md`,
  `docs/agents/NANOBOT.md`;
- `docs/skills/README.md`, `docs/skills/codex.md`, `docs/skills/graphify.md`,
  `docs/skills/nanobot.md`, `docs/skills/obsidian-layer-triage-kanban.md`,
  `docs/skills/obsidian.md`;
- `docs/runbooks/approved-live-apply.md`,
  `docs/runbooks/observe-propose-verify.md`,
  `docs/runbooks/proposal-review.md`, `docs/runbooks/sandbox-indexing.md`;
- `docs/acceptance/index.md`, `docs/obsidian-review-dashboard/index.md`;
- `docs/report-template.md`, `docs/telegram-summary-templates.md`;
- активный каталог `specs/001-instruction-tree-tool-documentation/`.

При добавлении нового `canonical` или `active` рабочего документа этот список и
структурная проверка обновляются в том же срезе.

## История и доказательства

- `ROLE_NOTES.md` — историческая совместимость; текущие роли находятся в
  `docs/agents/`.
- `docs/spec-kit/` — прежний проектный слой. Документ может оставаться детальной
  историей или источником решения, но не обходит активную функцию под `specs/`.
- `docs/audits/` — датированные `evidence`; новый факт создаёт новый аудит.
- `out/` — локальные генерируемые доказательства, игнорируемые Git и не
  являющиеся политикой.

## Протокол изменения

1. Определите ближайший `AGENTS.md` и родительскую цепочку.
2. Назовите затронутые канонические и активные документы.
3. Измените код/документ и его тест в одном небольшом срезе.
4. Для `tools/*.py` обновите `docs/tools/INDEX.md`, семейную инструкцию и runbook
   при approved-write.
5. Для роли обновите контракт и handoff; runtime-состояние храните только в
   `docs/RUNTIME_STATUS.md`.
6. Если влияние отсутствует, запишите `documentation impact: none` с причиной.
7. Запустите узкую проверку, `git diff --check` и требуемый общий verify.

## Термины

- `canonical` — главный текущий источник по теме.
- `active` — действующее руководство, подчинённое каноническому источнику.
- `historical` — сохранённое прошлое решение без текущих полномочий.
- `evidence` — проверяемое доказательство, а не разрешение.
- Runbook — пошаговая инструкция операции с остановкой и откатом.
- Spec Kit — структура `spec → plan → checklist → tasks` для управляемой работы.
