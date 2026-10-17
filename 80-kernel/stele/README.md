# Stele — реестр архитектурных решений (ADR)

> Στήλη — каменная плита, на которой высекали декреты и законы для постоянного публичного учёта.
> Здесь система **Hypomnemata** документирует саму себя: каждое решение об устройстве vault'а высечено, датировано, обосновано и связано с инвариантами контракта (INV-1…21). Решения не переписываются молча — отменяются только новым ADR (статус «superseded ADR-NNNN»), как гейты INV-5: осознанно, не под давлением.

## Зачем

- **INV-17 (система-как-код):** vault документирует собственную архитектуру внутри себя.
- **OwnerIntegrity (INV-2):** канонический источник архитектуры инструмента — здесь; рабочие карточки ссылаются на Стелу, а не дублируют решения.
- **Контракт:** инварианты `INV-1…21` — в [`contract.md`](contract.md) (канон; ADR ссылаются на `INV-N` туда).

## Формат

Один файл на решение: `ADR-NNNN-slug.md` по `../scaffolds/adr-tmpl.md`. Префикс `ADR-` — заглавный инвентарный префикс (ADR-0006) и средство глобальной находимости в Obsidian: quick-switcher, `[[` и поиск по «ADR» не зависят от папки. Слаг — строчная латиница, без пробелов, дефис. Статусы: `proposed` / `accepted` / `superseded ADR-MMMM` / `withdrawn`.

Частичная отмена не меняет статус ADR: она объявляется баннером в начале файла со ссылкой на отменяющий ADR, а в реестре — пометкой в скобках.

## Как читать Стелу в шаблоне

Это снимок решений одного человека, с исходными номерами и датами. Эволюция сохранена намеренно: superseded-решения и отменённые пункты остаются на месте, потому что довод «почему мы отсюда ушли» стоит не меньше самого решения.

**Пропуски номеров (0028, 0039) — решения сугубо личного рода, выброшенные из шаблона.** Номера не переиспользованы, чтобы ссылки между ADR и история не съезжали. Свои решения продолжайте с 0042.

Порядок чтения для знакомства: 0001 → 0002 → 0006 → 0009 → 0010 → 0019 → 0034 → 0035 → 0036 → 0037 → 0040. Остальное — по мере того, как упираетесь в соответствующий механизм.

## Реестр

| # | Решение | Статус | Дата | Инварианты |
|---|---------|--------|------|-----------|
| [0001](ADR-0001-vault-as-substrate.md) | Vault — единственный субстрат; тонкий слой поведения над Claude Code | accepted | 2026-06-25 | INV-1 INV-3 INV-4 INV-7 |
| [0002](ADR-0002-topology-mono-kernel.md) | Топология: гибрид моно-ядро + dot-внешнее | accepted | 2026-06-25 | INV-1 INV-7 INV-8 |
| [0003](ADR-0003-name-hypomnemata.md) | Имя системы — Hypomnemata | accepted | 2026-06-25 | INV-11 |
| [0004](ADR-0004-templates-in-kernel.md) | Шаблоны в ядре (`80-kernel/`), не в библиотеке | accepted | 2026-06-25 | INV-13 INV-17 INV-19 |
| [0005](ADR-0005-plugin-curation.md) | Курирование Obsidian-плагинов (native-first) | accepted | 2026-06-25 | INV-3 INV-4 INV-18 |
| [0006](ADR-0006-naming-convention.md) | Конвенция именования (каталоги + файлы) | accepted | 2026-06-25 | INV-17 INV-18 |
| [0007](ADR-0007-plugins-in-git.md) | Код плагинов Obsidian в git | accepted | 2026-06-25 | INV-1 |
| [0008](ADR-0008-workspace-layout-via-snapshot.md) | Раскладка через снимок Workspaces (не живой workspace.json) | accepted | 2026-06-25 | INV-1 INV-3 |
| [0009](ADR-0009-claude-machinery-in-dotclaude.md) | Вся машинерия Claude Code (включая `CLAUDE.md`) в `.claude/` | accepted | 2026-06-25 | INV-17 INV-18 |
| [0010](ADR-0010-memory-in-repo-native-config.md) | Память в репо через нативный `autoMemoryDirectory` (git вместо sync-хуков) | accepted | 2026-06-25 | INV-1 INV-7 INV-17 |
| [0011](ADR-0011-lightweight-orz-commands.md) | Облегчённые ОРЗ-протоколы как skills (`.claude/skills`, manual-only; ритуалы стратегирования позже слиты ADR-0037) | accepted | 2026-06-25 | INV-9 INV-10 INV-7 |
| [0012](ADR-0012-metadata-convention.md) | Конвенция метаданных (свойства — английские, теги и контент — ru-first) | accepted | 2026-06-25 | INV-17 INV-18 |
| [0013](ADR-0013-wp-card-self-contained.md) | Карточка РП: self-contained контекст + предъявимый артефакт (уточнён ADR-0036) | accepted | 2026-06-25 | INV-1 INV-2 INV-14 |
| [0014](ADR-0014-template-kinds.md) | Два рода шаблонов: Templater (пользователь) ≠ agent-скелет | accepted | 2026-06-26 | INV-4 INV-18 INV-19 |
| [0015](ADR-0015-resource-tracker.md) | Трекер источников (R-NNN) + политика слотов саморазвития (уточнён ADR-0020) | accepted | 2026-06-26 | INV-9 INV-13 INV-14 |
| [0016](ADR-0016-strategy-document.md) | Документ-стратегия (миссия / видение / цели / состояние; рамка периодов — ADR-0037) | accepted | 2026-06-26 | INV-2 INV-10 INV-14 |
| [0017](ADR-0017-principles-submodules-mcp.md) | Принципы (ZP/FPF/SPF) в `.principles/` + MCP mim-knowledge (опц.; механизм submodule снят ADR-0038) | accepted | 2026-06-26 | INV-1 INV-6 INV-7 |
| [0018](ADR-0018-installation-config.md) | Конфиг установки (`80-kernel/config.md`, дробление по потребителю) | accepted | 2026-06-27 | INV-1 INV-3 INV-18 |
| [0019](ADR-0019-pre-commit-framework.md) | Git-гейты через pre-commit framework + frontmatter-гейт | accepted | 2026-06-27 | INV-1 INV-5 INV-17 INV-18 |
| [0020](ADR-0020-resource-state-in-cards.md) | Состояние источника живёт в карточке (трекер = тонкая витрина) | accepted | 2026-06-28 | INV-1 INV-3 INV-18 |
| [0021](ADR-0021-dissatisfaction-archive.md) | Решённые неудовлетворённости → подкаталог `archive/` | accepted | 2026-06-29 | INV-3 INV-17 INV-18 |
| [0022](ADR-0022-work-governance-domain.md) | Наёмная работа как вложенный governance-домен (`11-governance-work/<employer>/`, опц.) | accepted | 2026-06-29 | INV-1 INV-3 INV-14 INV-18 INV-19 |
| [0023](ADR-0023-systems-registry.md) | Реестр развиваемых систем (`10-governance/9-systems/`, SYS-NNN; приватный дом ADR) | accepted | 2026-06-29 | INV-1 INV-2 INV-3 INV-7 INV-8 INV-14 INV-17 INV-19 |
| [0024](ADR-0024-global-claude-conventions-dotfiles.md) | Сквозные агент-конвенции в user-scope `~/.claude/CLAUDE.md` через dotfiles (п.3 об атрибуции отменён ADR-0041) | accepted | 2026-07-03 | INV-2 INV-3 INV-18 |
| [0025](ADR-0025-learn-note-alias-convention.md) | Конвенция alias учебных заметок + свойства источника `short`/`provider` | accepted | 2026-07-08 | INV-1 INV-3 INV-18 INV-19 |
| [0026](ADR-0026-personal-profile-corporate-boundary.md) | Граница личного и рабочего внутри одного дерева (хук + журнал отказов) | superseded ADR-0027 | 2026-08-04 | INV-2 INV-3 INV-18 |
| [0027](ADR-0027-knowledge-core-submodule.md) | Инвариантное обезличенное ядро знаний, общее для двух экзокортексов (опц.; механизм submodule снят ADR-0038) | accepted | 2026-08-07 | INV-1 INV-2 INV-3 INV-7 INV-8 INV-18 INV-19 |
| [0029](ADR-0029-time-tracking-instrument.md) | Прибор учёта времени: local-first (Super Productivity), vault = управление, прибор = исполнение (п.7 отменён ADR-0040) | accepted | 2026-08-09 | INV-1 INV-2 INV-8 INV-15 INV-18 |
| [0030](ADR-0030-repos-root-per-machine.md) | Корень раскладки клонов — свойство машины (путь спрашиваем у инструмента, уточняет 0002/0022) | accepted | 2026-08-10 | INV-1 INV-3 INV-18 |
| [0031](ADR-0031-project-mirrored-in-time-tracker.md) | Проект заводится и в приборе учёта времени (зеркало 1:1, номер от vault — уточняет 0029) | accepted | 2026-08-28 | INV-2 INV-3 INV-15 INV-18 |
| [0032](ADR-0032-cadence-rituals-and-forreview.md) | Ритуалы стратегирования по каденциям и лоток выноса (ритуалы слиты в `/strategize` ADR-0037) | accepted | 2026-09-05 | INV-2 INV-3 INV-5 INV-9 INV-10 INV-17 |
| [0033](ADR-0033-wp-mirrored-in-time-tracker.md) | Работы задачи зеркалятся в приборе учёта (хук-напоминание + недельный детектор; уточнён ADR-0036) | accepted | 2026-09-12 | INV-2 INV-3 INV-15 INV-17 INV-18 |
| [0034](ADR-0034-enforcement-independent-of-tool.md) | Энфорсмент независим от инструмента записи (PostToolUse-страж поверх PreToolUse-гейтов) | accepted | 2026-09-12 | INV-5 INV-17 INV-18 |
| [0035](ADR-0035-aspiration-tier-and-chain.md) | Ярус устремлений и цепочка, проверяемая только вниз (правит INV-14; п.3–5, 15 отменены ADR-0040) | accepted | 2026-09-20 | INV-2 INV-3 INV-6 INV-14 INV-17 INV-18 |
| [0036](ADR-0036-task-as-atomic-card.md) | Задача как атомарная карточка (`WP-NNN` → `T-NNN`); работа живёт в приборе — уточняет 0013/0033 | accepted | 2026-09-20 | INV-2 INV-3 INV-14 INV-15 INV-17 INV-18 |
| [0037](ADR-0037-sprint-unit-planning-frame.md) | Рамка планирования: спринт 12 недель · юнит 2 недели · разгрузочная; месяц и квартал сняты, ритуалы стратегирования слиты в `/strategize` (правит INV-9/INV-10) | accepted | 2026-09-24 | INV-3 INV-5 INV-9 INV-10 INV-17 INV-18 |
| [0038](ADR-0038-exocortex-shims-and-nested-repos.md) | Вложенные репозитории с исполняемым реестром вместо submodule; шимы между экзокортексами (опц.) | accepted | 2026-09-24 | INV-1 INV-2 INV-3 INV-7 INV-12 INV-17 INV-18 INV-19 |
| [0040](ADR-0040-project-is-the-goal.md) | Проект и есть цель: реестр целей сливается с реестром проектов, реестров пять (правит INV-14, отменяет ADR-0035 п.3–5, 15) | accepted | 2026-10-03 | INV-2 INV-3 INV-14 INV-17 |
| [0041](ADR-0041-no-ai-attribution-trailer.md) | Трейлеров атрибуции ИИ в коммитах нет (отменяет п.3 ADR-0024) | accepted | 2026-10-17 | INV-2 INV-3 |
