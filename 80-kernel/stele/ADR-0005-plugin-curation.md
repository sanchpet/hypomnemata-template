---
type: adr
status: accepted
created: 2026-06-25
context: сборка системы, Ф1 (перенос настроек)
invariants: [INV-3, INV-4, INV-18]
aliases: ["Курирование Obsidian-плагинов (native-first)", "ADR-0005"]
---

# ADR-0005 — Курирование Obsidian-плагинов (native-first)

## Контекст

Предыдущий vault нёс два десятка включённых плагинов, накопленных без ревизии. Переносим в новый не «весь `.obsidian/`», а курированно — каждая настройка проходит проверку «а Obsidian не умеет это сам?» (INV-18) и «зарабатывает ли место?» (INV-3).

## Решение

**Keep — несущие (контракт):** `dataview`, `templater-obsidian`, `meta-bind`, `homepage`. (`quickadd` выпилен 2026-06-30 — см. Амендмент.)

**Keep — QoL/служат письму:** `auto-link-title`, `url-into-selection`, `copy-url-in-preview`, `hover-editor`, `editing-toolbar`, `excalidraw`, `home-tab`, `style-settings` (тема Retroma), `obsidian-git` (ручной, без auto-commit).

**Drop — leave behind:** `buttons` (0 использований — улика: реальные карточки на Meta Bind), `excalibrain` (не начат), `obsidian-local-rest-api` (бэкенд obsidian-MCP → против INV-4), `claude-sidebar` (рантайм = Claude Code, не сайдбар), `friend-tracker` (вне домена), `obsidian42-brat`, `obsidian-html-plugin`, `media-notes`.

**Не-плагины:** переносим `hotkeys.json`, `types.json` (типы Properties), `appearance.json`, тема Retroma + нужные `snippets/`. Не переносим `workspace (N).json`, `.DS_Store`.

## Альтернативы

- **Скопировать весь `.obsidian/`** — отклонён: INV-3 (балласт накопленных лет), INV-4 (тащит `local-rest-api`/MCP-индирекцию, от которой ушли).

## Последствия

- + Минимальная поверхность; агент правит md напрямую без MCP.
- + `obsidian-git` без auto-commit — нет гонки с коммитами агента (INV-19).
- − Ручная проверка каждой настройки — цена осознанности (by design).

## Амендмент 2026-06-30 — `quickadd` выпилен

`quickadd` убран из несущих. Он был тонким диспетчером «кнопка → создать заметку из шаблона», но его конфиг жил в скрытом `.obsidian/plugins/quickadd/data.json` (вне версионируемого смысла), который при переносе из предыдущего vault рассинхронился и дважды дал сбой (старые пути из кеша). Функцию полностью несут уже-несущие **Meta Bind** (`templaterCreateNote`) + **Templater**: кнопка создания живёт в md-карточке (в репо), шаблон — в `80-kernel/templates`. Конфигурация создания стала версионируемой, без скрытого plugin-стейта (INV-1/3/18). Карточки-источники и шаблоны карточек мигрированы на Meta Bind; тип `note` слит в `learn-note`.
