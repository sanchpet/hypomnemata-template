---
type: readme
aliases: ["Машинерия: скрипты, хуки, конфиги"]
---

# Машинерия

Что исполняется в системе и где оно подключено. Носитель правил — Стела (`80-kernel/stele/`), здесь только карта исполнителей. Всё это — снимок устройства одной системы, а не поддерживаемый инструмент: берите, перекраивайте, выбрасывайте ненужное.

## Свежий клон

```bash
bash 80-kernel/scripts/bootstrap.sh
```

Нужны `git`, `python3` (3.9+) и [mise](https://mise.jdx.dev). Bootstrap ставит pre-commit через mise, выставляет права на скрипты и разворачивает вложенные репозитории из реестра `repos-bootstrap.sh`. Claude-хуки поднимаются из `.claude/settings.json` сами.

Перед первым запуском Claude Code поправьте `autoMemoryDirectory` в `.claude/settings.json`: в шаблоне стоит плейсхолдер `<vault-root>/70-memory`. Машинную дельту (другой корень клона на другой машине) кладите в `.claude/settings.local.json` — пример в `.claude/settings.local.json.example`, сам файл в `.gitignore` (ADR-0010, ADR-0030).

## Git-гейты (pre-commit, `.pre-commit-config.yaml`)

Срабатывают только на файлах коммита и ловят и агента, и ручную правку в Obsidian (ADR-0019).

| Хук | Скрипт | Что ловит |
|---|---|---|
| `frontmatter-check` | `frontmatter-check.py` | невалидный YAML и статус вне enum рода (ADR-0012) |
| `task-artifact` | `task-artifact-check.py` | задача с `unit:` без `artifact:` (ADR-0036 п.7) |
| `task-id-unique` | `task-id-unique-check.py` | один номер `T-NNN` у двух карточек (параллельные сессии) |
| `tray-outcome` | `tray-outcome-check.py` | слитый лоток со строкой без исхода либо с повторным переносом (ADR-0032 п.5) |
| `closed-date` | `closed-date-check.py` | закрытая задача/проект без верной даты `closed:` |
| `naming-convention` | `.claude/hooks/check-naming.sh` | имя файла не по ADR-0006 |

`hookgit.py` — общая часть гейтов, которые ловят акт, а не касание: история в HEAD не блокирует правку, `--strict` снимает поблажку для сверки всего реестра.

## Claude-хуки (`.claude/settings.json`)

| Событие | Хук | Роль |
|---|---|---|
| PreToolUse `Write\|Edit\|MultiEdit` | `check-naming.sh`, `check-task-artifact.sh` | блок до записи |
| PostToolUse пишущих тулов | `post-write-guard.sh` → `post-write-guard.py` | те же гейты для bash-пути записи, громким уведомлением (ADR-0034) |
| PostToolUse пишущих тулов | `task-mirror-remind.sh` | напоминание завести работу в приборе для новой карточки задачи (ADR-0033); **опционален** |
| SessionStart | `80-kernel/scripts/orz-check.sh` | положение в рамке спринта/юнита и пропуски ритма (INV-10, ADR-0037) |
| PreCompact | `precompact-checkpoint.sh` | напоминание сохранить `.claude/checkpoint.md` |
| UserPromptSubmit, PostToolUse, Stop | `wakatime-heartbeat.sh` | учёт времени агента в WakaTime; **опционален**, без `~/.wakatime/wakatime-cli` молчит |

Опциональный хук, который вам не нужен, снимается одной записью в `settings.json`.

## Детекторы и утилиты

- `orz-check.sh` — читает из `80-kernel/config.md` строки `strategy_day:` (день недели по-русски, умолчание — понедельник) и `sprint_epoch: YYYY-Www`. Без эпохи печатает только флаги дня, задач и памяти. Подмены для проверки на краснение: `ORZ_TODAY`, `ORZ_MEM_DIR`, `ORZ_MEM_MAX_ENTRIES`, `ORZ_MEM_MAX_CHARS`, `ORZ_REVIEW_DIR`.
- `chain-check.py` — разрывы цепочки неудовлетворённость → проект → задача, только вниз (INV-14, ADR-0035, ADR-0040). Отчёт, не гейт; нужен `pyyaml`.
- `task-mirror-check.py` — у каждой задачи юнита есть работа в приборе; показания прибора подаются на stdin сырым текстом. **Опционален** (Super Productivity).
- `week-time.py` — время ISO-недели из бэкапа Super Productivity в `10-governance/7-plans/current/week-time.md`, его читает `start.md`. **Опционален**; настройки (`timezone:`, `sp_invested_tag:`, `sp_role_prefix: "<префикс>"`) — в `config.md` либо в env, см. docstring. Запуск по расписанию — на ваш выбор (launchd, cron, systemd timer).
- `repos-bootstrap.sh [clone|pull]` — исполняемый реестр вложенных репозиториев вместо `.gitmodules`, fail-open (ADR-0038). В шаблоне — только публичная лестница принципов; свои репо дописывайте строкой `путь|адрес` и путём в `.gitignore`.
- `migrate-vault.py SRC DEST` — разовая миграция старого Obsidian-vault: транслит имён в slug, исходный заголовок в `aliases`. **Опционален.**

## Тесты

```bash
python3 -m pytest 80-kernel/scripts/tests      # либо без pytest:
python3 80-kernel/scripts/tests/test_tray_and_closed_checks.py
```

Каждый гейт доказан красным на плохой фикстуре и зелёным на хорошей — через тот же вход, что зовёт pre-commit.

## Obsidian

В шаблоне лежат только конфиги `.obsidian/*.json`; кода плагинов, их `data.json`, темы и сниппетов нет. Перечень плагинов — `.obsidian/community-plugins.json`. Чтобы их поставить:

1. Откройте vault в Obsidian → Settings → Community plugins → выключите Restricted mode.
2. Browse → найдите и установите каждый плагин из `community-plugins.json` (Dataview, Templater, Meta Bind, Homepage, Auto Link Title, Paste URL into selection, Image Context Menus, Hover Editor, Editing Toolbar, Excalidraw, Home tab, Style Settings, Git, Zotero Integration). Obsidian включит те, что перечислены в файле.
3. Настройте то, на что опирается система: Templater — Template folder location `80-kernel/templates`, Trigger Templater on new file creation — вкл.; Homepage — страница `start` (стартовая страница, INV-11); Dataview — включить JavaScript queries (их использует `start.md`).
4. `appearance.json` сброшен к умолчаниям Obsidian: тему и CSS-сниппеты выберите свои через Appearance.

Ненужный плагин (например, Zotero Integration без Zotero) удалите из `community-plugins.json`. Решите, версионировать ли код плагинов: автор держит его в git ради восстановимости из чистого клона (ADR-0007, INV-1).
