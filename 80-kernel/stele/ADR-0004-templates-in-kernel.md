---
type: adr
status: accepted
created: 2026-06-25
context: сборка системы, Ф1 (перенос настроек)
invariants: [INV-13, INV-17, INV-19]
aliases: ["Шаблоны в `kernel/`, не `library/`", "ADR-0004"]
---

# ADR-0004 — Шаблоны в `kernel/`, не `library/`

## Контекст

Где держать Templater-шаблоны (`book-tmpl`, `course-tmpl` + Meta Bind кнопки-генераторы). Первая прикидка — `library/` (рядом с выходом), пересмотрена.

## Решение

**`kernel/templates/`** (ныне `80-kernel/templates/`, [[ADR-0006-naming-convention|ADR-0006]]). Шаблон = машинерия (исполняемая оснастка: Templater-JS + Meta Bind + логика) → класс «код», не «заметка». Writer шаблона = агент/мейнтейнер (INV-19), не engineer-writer; под INV-17 (валидация схемы, контролируемый такт изменений). **Выход** шаблонов (карточки книг/курсов) → `library/` (engineer-writer).

## Альтернативы

- **`library/`** — отклонён: путает штамп с выходом (cookie-cutter ≠ cookie). Выход служит библиотеке, но сам штамп — машинерия.

## Последствия

- + Штамп под код-дисциплиной (INV-17), выход у писателя (INV-19) — чёткая граница writer-ownership.
- + Native-first держится: `kernel/` не dot-каталог → Templater читает `.md`-шаблоны как файлы vault.
- Уточнён [[ADR-0014-template-kinds|ADR-0014]]: agent-скелеты живут отдельно, в `80-kernel/scaffolds/`.
