---
type: adr
status: accepted
created: 2026-06-25
context: сборка системы, Ф3
invariants: [INV-9, INV-10, INV-7]
aliases: ["Облегчённые ОРЗ-протоколы как skills (`.claude/skills`, manual-only)", "ADR-0011"]
---

# ADR-0011 — Облегчённые ОРЗ-протоколы как skills (`.claude/skills`, manual-only)

> ⚙️ Позднейшие уточнения: ритуалы стратегирования разных каденций слиты в один `/strategize` с вычисляемым режимом — [[ADR-0037-sprint-unit-planning-frame|ADR-0037]]; `/for-review` — названное исключение из manual-only (model-invocable) — [[ADR-0032-cadence-rituals-and-forreview|ADR-0032]].

## Контекст

Нужен ритм ОРЗ (Открытие→Работа→Закрытие) на масштабах день/неделя (INV-9/10). Старые IWE-протоколы (open/close/work, ~13–22 тыс. строк каждый) тяжёлые: 4-местная регистрация рабочих продуктов, агрегация по чужим репо, субагент-верификация.

## Решение

ОРЗ — **облегчённые skills** (`.claude/skills/<name>/SKILL.md`) с `disable-model-invocation: true` (manual-only — Claude сам `/close` не запускает): `/open`, `/close`, `/strategize`. Читают реестры/планы vault, пишут DayPlan / session log / планы периода, делают capture-маршрутизацию (решение→Стела, урок→память, домен→knowledge, семя→library). По доке Claude Code кастомные commands **слиты в skills** — берём современную форму skills, не легаси-commands. Старые IWE-протоколы — **pull-by-need референс** (INV-7).

## Альтернативы

- **Портировать IWE-протоколы целиком** — отклонён: тяжесть + чужая обвязка (4-местная регистрация, агрегация по чужим репо, субагенты) против INV-7/INV-3.

## Последствия

- + Ритм работает нативно (`/open` / `/close` / `/strategize`), лёгкий, под личный vault.
- − Жёсткая детекция пропусков (INV-17: пропущенное стратегирование, разрыв цепочки) на момент решения — через Dataview-детектор (`index`) + проверку в `/open`, а не через отдельные enforcement-хуки — follow-up (позже закрыт детекторами `orz-check.sh`, `chain-check.py` и pre-commit-гейтами).
