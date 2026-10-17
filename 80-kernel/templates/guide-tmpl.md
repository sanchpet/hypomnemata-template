<%*
const rnum = await tp.system.prompt("R-номер (R-NNN):");
const slug = await tp.system.prompt("Английский slug:");
const ruTitle = await tp.system.prompt("Русское название:");
const short = await tp.system.prompt("Короткое имя (для суффикса alias заметок):", ruTitle);
const provider = await tp.system.prompt("Провайдер (МИМ/…; пусто — Enter):", "");
const provLine = provider ? `provider: ${provider}\n` : "";
await tp.file.move("20-library/resources/3-guides/" + rnum + "-" + slug);
-%>
---
id: <% rnum %>
short: <% short %>
<% provLine %>type: guide
status: in-progress
started: <% tp.date.now("YYYY-MM-DD") %>
aliases: ["<% ruTitle %>"]
---
[Название::<% ruTitle %>]
***

## О руководстве

- **Источник:** <% ruTitle %>.
- **Слот:** входит в слот саморазвития.
- **Связь:** <DIR-N · проект PNN · Vision>.

## Разделы

- <ключевые разделы / практики руководства>

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

| Неделя | Что прошёл (раздел) | Часов | Заметки |
|--------|--------------------|-------|---------|
|        |                    |      |         |
