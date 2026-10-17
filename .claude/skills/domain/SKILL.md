---
name: domain
description: "Создание паспорта предметной/доменной области по модели SPF (guided flow): тест домен≠тема, имя, bounded context, scaffold структуры из .principles/spf/pack-template, дорожная карта наполнения. Артефакт — 30-knowledge/<slug>/ (НЕ PACK)."
argument-hint: "[область знания или домен]"
disable-model-invocation: true
---

# /domain — паспорт домена по SPF

Создаём паспорт домена: $ARGUMENTS

## Что делает / НЕ делает

- **Делает:** ведёт по SPF §01-02, предлагает имя, ставит структуру из `.principles/spf/pack-template`, даёт дорожную карту наполнения.
- **НЕ делает:** не заполняет содержанием (это ручная работа по `.principles/spf/process/03-11` + capture на `/close`); GitHub-репо не нужен — паспорт живёт в этом vault.

> Модель и шаблоны — вложенный репозиторий `.principles/spf` (`pack-template/` + `process/`), разворачивает `bash 80-kernel/scripts/repos-bootstrap.sh clone` (ADR-0038). Нет каталога — сначала развернуть. Никакого префикса `PACK` (наш термин — «паспорт домена», `30-knowledge/`, INV-20).

## Шаг 1. Домен ≠ Тема (SPF §01)

Задать ОДНИМ сообщением 3 вопроса:

1. **Кто практикует домен?** (роль/профессия)
2. **Что производят?** (артефакты, рабочие продукты)
3. **Как типично ошибаются?** (3-5 failure modes)

«Интересуюсь темой X» → объяснить: тема = область интереса без своих методов/артефактов; домен = практика с методами, продуктами и failure modes. Тест: «есть ли те, кто ДЕЛАЕТ это профессионально, и что производят?». Затрудняется → до 2 уточняющих.

**Новый паспорт vs расширить существующий** — по `.principles/spf/spec/SPF.SPEC.005-boundary-rules.md` (бинарные гейты «это один BoundedContext или два?», без количественных порогов). Дубль 80% соседнего паспорта = расширять, не заводить новый (Pack-fork). Имя-глагол = не домен (Pack-process). Один метод без рабочих продуктов = ещё не паспорт (Pack-thin).

## Шаг 2. Имя домена (SPF §01 §4)

Существительное, узнаваемое практикам. Критерии: специфично (исключает соседние домены), широко (ядро методов, не один инструмент), узнаваемо, slug — латиница kebab-case ≤30. **Без `PACK-`.** Папка: `30-knowledge/<slug>/`.

Предложить 2-3 варианта → выбор пользователя. Антипримеры: `everything` (широко), `jira` (инструмент), `notes` (нет практики).

## Шаг 3. Bounded Context (SPF §02)

Заполнить с пользователем (шаблон `.principles/spf/pack-template/01-domain-contract/01A-bounded-context.md`): scope (что внутри/снаружи), ubiquitous language (ключевые термины), соседние домены и границы.

## Шаг 4. Scaffold структуры

Создать `30-knowledge/<slug>/` по `.principles/spf/pack-template/`, **переименовав файлы под ASCII-конвенцию (ADR-0006) и убрав «pack» из имён** (`00-pack-manifest.md` → `00-manifest.md`).

Полная структура SPF: `00-manifest`, `01-domain-contract` (bounded-context + distinctions), `02-domain-entities` (roles / objects / methods-index / tools-index / characteristics), `03-methods`, `04-work-products`, `05-failure-modes`, `06-sota`, `07-map`, `08-service-clauses`.

**Минимально жизнеспособный паспорт (INV-3) — начать подмножеством:** `00-manifest` + `01-domain-contract` + `02-domain-entities` (roles/objects) + `03-methods` + `04-work-products` + `05-failure-modes`. Разделы `06-sota` / `07-map` / `08-service-clauses` — по мере роста, не сразу. Спросить пользователя: полный scaffold или минимальный.

frontmatter заметок паспорта — по ADR-0012 (`type`, `aliases` с русским названием).

## Шаг 5. Дорожная карта наполнения

По `.principles/spf/process/` (00-overview → 11-review): показать шаги наполнения (различения §03 → сущности §04 → ingestion §05 → формализация §06 → методы/продукты §07 → failure-modes §08 → sota §09 → map §10) с грубыми оценками. Наполнение — отдельная работа (задача по `task-discipline`, `/task-new`), не в этом скилле.

## Выход

Структура паспорта в `30-knowledge/<slug>/` + дорожная карта. Капчур знания при наполнении — через `/close`. Эволюция/ревизия паспорта — `.principles/spf/process/11-review-and-evolution-cycle.md`.
