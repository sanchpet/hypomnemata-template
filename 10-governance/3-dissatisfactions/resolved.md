---
type: dissatisfaction-archive
status: resolved
aliases: [Решённые неудовлетворённости]
---

# Решённые неудовлетворённости

> Архив решённых неудовлетворённостей — для истории и обоснования проектов ([[ADR-0021-dissatisfaction-archive|ADR-0021]]). Решённая карточка переносится в `archive/` со `status: resolved` и полем `resolved: YYYY-MM-DD`: файл сохраняет wikilinks из проектов и задач (INV-18), индекс — Dataview ниже.
>
> Если вы мигрируете из прежней системы, решённые записи до введения правила можно держать здесь таблицей без файлов — у автора так живут первые записи реестра.

## Решённые (заметки в `archive/`)

```dataview
TABLE WITHOUT ID file.link AS "Неудовлетворённость", area AS "Область", resolved AS "Решено"
FROM "10-governance/3-dissatisfactions/archive"
WHERE type = "dissatisfaction"
SORT resolved DESC
```
