---
type: registry-index
aliases: [Реестр, Карта]
---

# Реестр — карта (INV-14)

> Это **вид** (Dataview) поверх frontmatter заметок, не дубль. Цепочка ([[ADR-0035-aspiration-tier-and-chain|ADR-0035]], [[ADR-0040-project-is-the-goal|ADR-0040]]): **направление → устремление → неудовлетворённость → проект → задача**; проект и есть цель. Каждый объект называет только своего родителя; проверка идёт **только вниз** — устремление без неудовлетворённости есть свидетельство покоя, а не разрыв.

## Неудовлетворённости (активные)

```dataview
TABLE WITHOUT ID file.link AS "Неудовлетворённость", link(aspiration, aspiration.aliases[0]) AS "Устремление", driver_type AS "Тип"
FROM "10-governance/3-dissatisfactions"
WHERE type = "dissatisfaction" AND status = "active"
SORT file.name
```

> Решённые → [[resolved]].

## Устремления по направлениям

```dataview
TABLE WITHOUT ID link(file.link, file.aliases[0]) AS "Устремление", link(direction, direction.aliases[0]) AS "Направление"
FROM "10-governance/2-aspirations"
WHERE type = "aspiration"
SORT direction, id
```

## Проекты-цели — с критерием

> Критерий назначен — проекту законно выделять время юнита ([[ADR-0040-project-is-the-goal|ADR-0040]]).

```dataview
TABLE WITHOUT ID link(file.link, file.aliases[0]) AS "Проект", default(dissatisfaction, aspiration) AS "Родитель", criterion AS "Критерий", period, budget_h AS "Бюджет, ч", status
FROM "10-governance/5-projects" AND !"10-governance/5-projects/archive"
WHERE type = "project" AND criterion
SORT period DESC, id ASC
```

## Проекты без критерия — русла и кандидаты на снятие

> Отсутствие критерия законно для бессрочного русла (`scope: infinite`), но время юнита ему не выделяется. **Список читается на шаге 4 сессии как список кандидатов на снятие** — проект, которому из спринта в спринт не находится критерия, скорее всего не нужен вовсе, и честнее его закрыть, чем держать в реестре живым. Решение о снятии принимается владельцем, а не выводится из пустого поля.

```dataview
TABLE WITHOUT ID link(file.link, file.aliases[0]) AS "Проект", default(dissatisfaction, aspiration) AS "Родитель", status, scope, priority_updated AS "Приоритет трогали"
FROM "10-governance/5-projects" AND !"10-governance/5-projects/archive"
WHERE type = "project" AND !criterion
SORT priority_updated ASC, id ASC
```

## Детектор разрыва цепочки (INV-17)

> Проверка **только вниз**: каждый объект обязан назвать старшего. Обратной проверки нет — устремление без неудовлетворённости, неудовлетворённость без проекта и проект без задач суть законные состояния покоя, а не разрывы. Не прошедшее выносится строкой в лоток с вопросом владельцу, а не отбраковывается (ADR-0035 п.7).

### Неудовлетворённость без устремления

```dataview
LIST
FROM "10-governance/3-dissatisfactions"
WHERE type = "dissatisfaction" AND status = "active" AND !aspiration
```

### Проект без родителя

```dataview
LIST
FROM "10-governance/5-projects" AND !"10-governance/5-projects/archive"
WHERE type = "project" AND status = "active" AND !dissatisfaction AND !aspiration
```

### Время выделено проекту без критерия

> Бессрочное русло **не обязано** иметь критерий ([[ADR-0040-project-is-the-goal|ADR-0040]] п.5). Краснеет другое — когда проекту уже выделено время юнита, а критерия у него нет. Наблюдается со стороны живой задачи: взята в юнит, а её проект без критерия; закрытые задачи задним числом не перепроверяются.

```dataview
LIST "проект без критерия, а задача взята в юнит: " + project
FROM "10-governance/6-tasks"
WHERE type = "task" AND unit AND !project.criterion AND !contains(list("done", "closed", "dropped"), status)
```

### Задача без проекта

```dataview
LIST
FROM "10-governance/6-tasks"
WHERE type = "task" AND !project
```
