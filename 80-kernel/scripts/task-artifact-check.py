#!/usr/bin/env python3
"""Гейт рабочего продукта: задача, взятая в юнит, обязана его назвать (ADR-0013, уточнён ADR-0036 п.7).

Триггер — **не заведение карточки, а взятие в юнит**. Задача есть действие внутри
проекта, и рабочий продукт у неё желателен; обязательным он становится там, где
задача превращается в работу, то есть когда заполнено поле `unit:`. Без шестого
поля формулировки работы нет.

Задача без `unit:` проходит молча, и это правильно: она ещё не запланирована.

Рабочий продукт есть **изменение в мире**, не обязательно документ: у задачи
«позвонить в клинику и записаться» рабочий продукт — назначение на явку.

Вход: имена файлов аргументами (pre-commit передаёт staged-файлы) ИЛИ markdown
из stdin (fallback, PreToolUse-хук).
Exit 0 — всё в порядке; exit 2 — задача юнита без рабочего продукта.

see 80-kernel/stele/ADR-0013-wp-card-self-contained.md · ADR-0036-task-as-atomic-card.md
"""
import sys, re


def field(fm, name):
    m = re.search(rf'^{name}:\s*(.*)$', fm, re.M)
    if not m:
        return ''
    return m.group(1).strip().strip('"').strip("'").strip()


def check(txt, label):
    m = re.match(r'---\n(.*?)\n---', txt, re.S)
    if not m:
        # Без frontmatter нельзя узнать ни юнит, ни продукт — карточка недоформлена.
        return f"{label}: карточка задачи без frontmatter (нет ни `unit:`, ни `artifact:`)."
    fm = m.group(1)

    # Не взята в юнит — гейт молчит: рабочий продукт пока желателен, не обязателен.
    if not field(fm, 'unit'):
        return None

    val = field(fm, 'artifact')
    if not val:
        return (f"{label}: ADR-0036 п.7 — задача взята в юнит, но рабочий продукт не назван. "
                "Формулировка работы состоит из шести полей, и шестое — результат. "
                "Заполни `artifact:` — изменение в мире, которое останется после работы "
                "(файл, репо, сервис, документ, назначенная явка, принятое решение), "
                "не деятельность («отслушал», «разобрался»). "
                "Тест: «что изменится в мире, когда работа сделана?»")
    if '<' in val and '>' in val:
        return f"{label}: ADR-0036 п.7 — поле artifact = незаполненный плейсхолдер шаблона ({val})."
    return None


errs = []
if len(sys.argv) > 1:
    for p in sys.argv[1:]:
        try:
            with open(p, encoding='utf-8') as f:
                txt = f.read()
        except OSError as e:
            errs.append(f"{p}: не прочитан ({e})")
            continue
        e = check(txt, p)
        if e:
            errs.append(e)
else:
    e = check(sys.stdin.read(), "<stdin>")
    if e:
        errs.append(e)

if errs:
    for e in errs:
        sys.stderr.write(e + "\n")
    sys.exit(2)
sys.exit(0)
