---
type: index
aliases: ["Реестр систем", "Systems"]
---

# Реестр систем (SYS-NNN)

> Эксплуатируемые и развиваемые системы как durable-артефакты (≠ проекты: система существует и эволюционирует; проект — работа к исходам) — [[ADR-0023-systems-registry|ADR-0023]]. Каталог параллельный, а не шестой реестр цепочки (INV-14 не трогается). Native-first и легко: папка + карточки + этот Dataview, без машинерии (INV-3/7). `SYS-000` — сама система.

**Приватный канонический дом ADR внешней системы — здесь**, в `9-systems/SYS-NNN-<slug>/adr/`, а **не** в её (часто публичном) репозитории: ADR раскрывают топологию, провайдера, юрисдикцию секретов (opsec). Архитектурные решения самого vault остаются в Стеле `80-kernel/stele/`.

**Раскладка системы:**

```
9-systems/
  SYS-NNN-<slug>/
    SYS-NNN-<slug>.md      # карточка системы
    adr/ADR-NNNN-<slug>.md # её решения, своя нумерация
    operations-notes.md    # технические факты эксплуатации — носитель, на который память шлёт технику (ADR-0010)
```

**Схема карточки:**

```yaml
---
type: system
id: SYS-NNN
status: active
aliases: ["<имя>", SYS-NNN]
repo: "<owner>/<repo> — или «нет»"
created: YYYY-MM-DD
---
```

```dataview
TABLE status, repo, id
FROM "10-governance/9-systems"
WHERE type = "system"
SORT id ASC
```
