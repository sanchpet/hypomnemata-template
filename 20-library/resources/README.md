# 20-library/resources — источники образования (R-NNN)

Карточка источника — **единственный владелец его состояния** (ADR-0020): темы, расписание, прогресс дробью против полного объёма. Витрина над карточками — [[resources-tracker]]. Класс карточки — `mixed` (INV-19): таблицу «Прогресс» ведёт агент (`80-kernel/docs/learning-progress.md`), прозу — владелец.

| Каталог | Род (`type`) | Шаблон |
|---|---|---|
| `1-books/` | `book` | `80-kernel/templates/book-tmpl.md` |
| `2-courses/` | `course` | `course-tmpl.md` |
| `3-guides/` | `guide` | `guide-tmpl.md` |
| `4-sources/` | `source` — стрим, сообщество, лаба, канал | `source-tmpl.md` |
| `9-notes/` | `learn-note` и разобранные `finding` / `conversation` | `learn-note-tmpl.md` — кнопкой с карточки источника |
| `annotations/` | `source-annotations` — пометки из Zotero (опционально) | `zotero-annotations-tmpl.md` |

Имя карточки — `R-NNN-<slug>.md`; заметки по источнику — `rNNN-NN.md`, alias по формату ADR-0025: «Тема (эмодзи-род short @provider · R-NNN)». Род берётся из свойства `type`, а не из папки.
