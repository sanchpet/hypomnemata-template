<%*
const rnum = await tp.system.prompt("R-номер (R-NNN):");
const slug = await tp.system.prompt("Английский slug:");
const ruTitle = await tp.system.prompt("Русское название:");
const short = await tp.system.prompt("Короткое имя (для суффикса alias заметок):", ruTitle);
const provider = await tp.system.prompt("Провайдер — сообщество, канал, площадка (пусто — Enter):", "");
const provLine = provider ? `provider: ${provider}\n` : "";
await tp.file.move("20-library/resources/4-sources/" + rnum + "-" + slug);
-%>
---
id: <% rnum %>
short: <% short %>
<% provLine %>type: source
status: active
started: <% tp.date.now("YYYY-MM-DD") %>
aliases: ["<% ruTitle %>"]
---
[Название::<% ruTitle %>]
***

## Об источнике

- **Что это:** <% ruTitle %> — <стрим / сообщество / лаба / канал>.
- **Слот:** входит в слот саморазвития.
- **Связь:** <DIR-N · проект PNN · Vision>.

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

| Неделя | Что прошёл | Часов | Заметки |
|--------|-----------|-------|---------|
|        |           |      |         |
