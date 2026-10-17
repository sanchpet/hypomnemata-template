---
type: source-annotations
citekey: {{citekey}}
title: "{{title | replace('"', "'")}}"
authors: "{{authors | replace('"', "'")}}"
year: {{date | format("YYYY")}}
zotero: {{desktopURI}}
imported: {{importDate | format("YYYY-MM-DD")}}
aliases: ["{{title | replace('"', "'")}}"]
---

# {{title}}

> Пометки на полях из Zotero — сырьё для учебной заметки ([[en-2-learn-notes|EN-2]]), не сама заметка. Повторный импорт перезаписывает пометки; свои мысли — в учебной заметке, а блок «Свои строки» ниже переживает импорт.

{% persist "own" %}{% if isFirstImport %}## Свои строки

{% endif %}{% endpersist %}

## Пометки
{% for a in annotations %}
- {% if a.annotatedText %}«{{a.annotatedText}}»{% endif %}{% if a.imageRelativePath %} ![[{{a.imageRelativePath}}]]{% endif %} — [с. {{a.pageLabel}}](zotero://open-pdf/library/items/{{a.attachment.itemKey}}?page={{a.page}}&annotation={{a.id}}){% if a.comment %}
	- {{a.comment}}{% endif %}
{% endfor %}
