<%*
const rnum = await tp.system.prompt("R-номер (R-NNN):");
const slug = await tp.system.prompt("Английский slug:");
const ruTitle = await tp.system.prompt("Русское название:");
const short = await tp.system.prompt("Короткое имя (для суффикса alias заметок):", ruTitle);
const autor = await tp.system.prompt("Автор:");
await tp.file.move("20-library/resources/1-books/" + rnum + "-" + slug);
-%>
---
id: <% rnum %>
short: <% short %>
type: book
status: in-progress
started: <% tp.date.now("YYYY-MM-DD") %>
aliases: ["<% ruTitle %>"]
---
[Автор::[[<% autor %>]]] | [Название::<% ruTitle %>]
***

## О книге

- **Автор:** <% autor %>.
- **Слот:** входит в слот саморазвития.
- **Связь:** <DIR-N · проект PNN · Vision>.

## Краткие итоги чтения

- <главное, вынесенное из книги>

## Учебные заметки

```meta-bind-button
label: Создать заметку
icon: ""
hidden: false
class: ""
tooltip: ""
id: ""
style: default
actions:
  - type: templaterCreateNote
    templateFile: 80-kernel/templates/learn-note-tmpl.md
    folderPath: 20-library/resources/9-notes
    openNote: true
```

```dataview
TABLE rows.file.cday AS "Дата"
FROM [[]] WHERE type = "learn-note"
GROUP BY link(file.link, regexreplace(file.aliases[0], " \([^()]*\)$", "")) AS "Заметка"
sort rows.file.ctime ASC
```

## Прогресс

| Неделя | Что прошёл (главы) | Часов | Заметки |
|--------|-------------------|-------|---------|
|        |                   |      |         |
