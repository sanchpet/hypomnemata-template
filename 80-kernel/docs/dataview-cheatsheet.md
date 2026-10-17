---
aliases:
  - dataview
  - Dataview
tags:
  - справка
  - системное
---
### Полезные ссылки на документацию
- [Dataview](https://blacksmithgu.github.io/obsidian-dataview/)
- [Dataview in Obsidian: A Beginner's Guide - Obsidian Rocks](https://obsidian.rocks/dataview-in-obsidian-a-beginners-guide/)
- [Super Powers for Obsidian: Nine of the Best Obsidian Plugins - Obsidian Rocks](https://obsidian.rocks/super-powers-for-obsidian-nine-of-the-best-obsidian-plugins/)
- [Quickly Organize Notes in Obsidian - Obsidian Rocks](https://obsidian.rocks/quick-tip-quickly-organize-notes-in-obsidian/)
- [Creating Dynamic Graphs in Obsidian - Obsidian Rocks](https://obsidian.rocks/creating-dynamic-graphs-in-obsidian/)
- [Getting Started with Zettelkasten in Obsidian - Obsidian Rocks](https://obsidian.rocks/getting-started-with-zettelkasten-in-obsidian/)
- [An Introduction to Dataview - Obsidian Hub - Obsidian Publish](https://publish.obsidian.md/hub/04+-+Guides%2C+Workflows%2C+%26+Courses/Guides/An+Introduction+to+Dataview)

# Язык запросов
## Представление информации
Представлять информацию можно в 4 видах:
- TABLE
- LIST
- TASK
- CALENDAR
## Источники информации
Ключевое слово `FROM` задаёт область для поиска файлов/задач для отображения. Какие есть источники:
- Тэги #справка
- Папки и файлы: "Путь/К/Папке/Файлу"
- Ссылки: [[]] – для заметок, ссылающихся на этот файл или outgoing([[]]) – для исходящих ссылок
С помощью операторов `AND` и `OR` и скобок выражения можно комбинировать, исключение работает через `-` (-#выполнено).
## Фильтрация результатов
Фильтрация результатов производится при помощи `WHERE`
### Фильтрация по содержимому
- meta(section).subpath - фильтрация по наличию подзаголовка
- icontains(text, "#купить") - фильтрация по содержанию текста в заметке
- !icontains - отрицание содержания (не содержит)
### Фильтрация по статусу задачи
Для тасков можно производить фильтрацию по статусу выполнения: !completed или completed. 
## Сортировка результатов
Сортировка результатов производится при помощи `SORT` и параметра сортировки: `ASC`/`DESC`
## Управление результатами
Можно ограничить результаты словом `LIMIT`.
`GROUP BY` может объединить результаты на основе условия.
В таблице можно использовать `FLATTEN` для деления результатов по папкам. 
# Метаданные
Плагин по умолчанию имеет доступ к следующим метаданным:
- file.name – названию файла
- file.folder – названию папки
- file.path – путь к файлу
- file.ext – расширение файла
- file.link – ссылка на файл
- file.size – размер файла
- file.ctime – дата и время создания
- file.cday – дата создания
- file.mtime – дата и время редактирования
- file.mday – дата редактирования
- file.tags – список тэгов в заметке (вложенные тэги `#статус/выполнено` видятся как несколько тэгов: `#статус` и `#статус/выполнено` )
- file.etags – список тэгов в заметке (вложенные тэги видятся как один тэг – только `#статус/выполнено`)
- file.inlinks – список входящих ссылок
- file.outlinks – список исходящих ссылок
- file.aliases – список псевдонимов
- file.tasks – список задач в заметке
- file.lists – список всех элементов всех списков в заметке
- file.frontmatter – список всех метаданных из frontmatter
- file.day – дата, в случае если файл имеет формат наименования yyyy-mm-dd, или если в заметке есть пользовательское поле метаданных с названием Date
## Использование своих метаданных
Как включать метаданные в текст:
- использовать двойное двоеточие в паре «ключ::значение» для новых строк и «[ключ::значение]» или «(ключ::значение)» – для метаданных посреди другого текста; 
- либо одинарное двоеточие во frontmatter «ключ:значение»

Значения метаданных могут быть следующих видов:
- Текст: «привет»
- Число: 43
- Логическое ИСТИНА или ЛОЖЬ: true, false
- Дата: 2023-06-01
- [Продолжительность](https://blacksmithgu.github.io/obsidian-dataview/annotation/types-of-metadata/#duration): 7 hours, 9 yrs 8 min
- Вики-ссылка
- Список (содержащий другие значения, например список чисел)

# Внутристроковые запросы
Составляются при помощи одинарных кавычек и символа =. Пример запроса на отображение текущей даты и времени: ==`=dateformat(date(now), "EEE D HH:mm")`==

