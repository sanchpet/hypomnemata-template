#!/usr/bin/env python3
"""Гейт пустого исхода лотка (pre-commit hook). ADR-0032 п.5, § Последствия.

Правило слива: к закрытию сессии каждая строка лотка получает исход
(✅ закрыта · ⬆️ поднята · ✂️ снята · ➡️ перенесена, перенос однажды), и слитый
лоток уходит из `plans/review/` в `plans/archive/`. Отсюда граница дефекта:

- лоток в `7-plans/review/` наполняется в течение периода — строки без исхода
  законны, гейт молчит;
- лоток в `7-plans/archive/` слит — строка без исхода означает непроведённый
  шаг сессии, гейт краснеет.

Гейт ловит акт, а не касание: краснеет на лотке, впервые входящем в архив
(новый файл либо перенос из `review/`), и на строке, потерявшей исход в уже
архивном. Пустоты, лежавшие в HEAD архивного лотка, — история, правке ссылок
она не мешает; `--strict` снимает эту поблажку для сверки всего архива.

Строка — ряд таблицы, в шапке которой есть столбец «Исход» (таблица, разорванная
пустой строкой, продолжается). Исход есть, только если ячейка после снятия разметки
начинается одним из четырёх маркеров; «⚙️ частично», «◐», «↪», тире и «без исхода»
исходом не считаются. Ряд-заглушка без предмета (пустой второй столбец либо «—»)
не считается. Перенос допустим однажды: ряд, внесённый переносом (столбцы между
предметом и исходом говорят «перенесена»), повторным ➡️ краснеет.

Вход: имена файлов аргументами (pre-commit передаёт staged-файлы); без
аргументов — выход 0 без чтения stdin. Exit 0 — чисто; exit 1 — пустые исходы.
"""
import re
import sys

import hookgit

ARCHIVE = re.compile(r"(^|/)7-plans/archive/(.*/)?[^/]*forreview[^/]*\.md$")
# Pipes inside wikilinks and inline code are not cell separators.
ATOMIC = re.compile(r"\[\[.*?\]\]|`[^`]*`")
MARKUP = re.compile(r"<!--.*?-->|<br\s*/?>|~~.*?~~|[*_`]")
FILLER = set("-—–−?…. ")
# Variation selector U+FE0F is optional: both "✅" and "➡️"/"➡" occur in trays.
MARKERS = ("✅", "⬆", "✂", "➡")
CARRY = "➡"
CARRIED_IN = re.compile(r"перенес[её]н", re.I)


def cells(line):
    masked = ATOMIC.sub(lambda m: "x" * len(m.group(0)), line.replace(r"\|", "xx"))
    bounds = [-1] + [i for i, ch in enumerate(masked) if ch == "|"] + [len(line)]
    row = [line[a + 1:b].strip() for a, b in zip(bounds, bounds[1:])]
    if row and not row[0]:
        row = row[1:]
    if row and not row[-1]:
        row = row[:-1]
    return row


def is_separator(row):
    return bool(row) and all(re.fullmatch(r":?-+:?", c) for c in row)


def is_blank(cell):
    core = MARKUP.sub("", cell).strip()
    return not core or set(core) <= FILLER


def outcome(cell):
    return MARKUP.sub("", cell).strip()


def lacks_outcome(cell):
    return not outcome(cell).startswith(MARKERS)


def carried_twice(row, col):
    """Ряд уже пришёл переносом и снова ➡️ перенесён."""
    return (outcome(row[col]).startswith(CARRY)
            and any(CARRIED_IN.search(c) for c in row[2:col]))


def empty_outcomes(txt):
    """[(номер строки файла, номер ряда лотка, причина)] для рядов без верного исхода."""
    lines = txt.splitlines()
    found, col = [], None
    for n, line in enumerate(lines, 1):
        s = line.strip()
        if not s.startswith("|"):
            if s:
                col = None
            continue
        row = cells(s)
        if is_separator(row):
            continue
        nxt = lines[n].strip() if n < len(lines) else ""
        if nxt.startswith("|") and is_separator(cells(nxt)):
            heads = [MARKUP.sub("", c).strip().lower() for c in row]
            col = next((k for k, h in enumerate(heads) if h.startswith("исход")), -1)
            continue
        if col is None or col < 0 or len(row) < 2 or is_blank(row[1]):
            continue
        if col >= len(row) or lacks_outcome(row[col]):
            found.append((n, row[0], "без исхода"))
        elif carried_twice(row, col):
            found.append((n, row[0], "перенесена повторно"))
    return found


def grandfathered(path, renames):
    """Ряды без исхода, уже лежавшие в HEAD этого архивного лотка."""
    source = hookgit.head_source(path, renames)
    if not ARCHIVE.search(source):
        return set()
    old = hookgit.head_text(source)
    return {(num, why) for _, num, why in empty_outcomes(old)} if old is not None else set()


def main(args):
    strict = "--strict" in args
    paths = [a for a in args if a != "--strict"]
    renames = {} if strict or not paths else hookgit.staged_renames()
    fails = []
    for path in paths:
        if not ARCHIVE.search(path.replace("\\", "/")):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                txt = f.read()
        except OSError as e:
            fails.append(f"{path}: не прочитан ({e})")
            continue
        old = set() if strict else grandfathered(path, renames)
        for n, num, why in empty_outcomes(txt):
            if (num, why) not in old:
                fails.append(f"{path}:{n}: строка лотка #{num} {why}")
    if fails:
        sys.stderr.write(
            "✗ Слитый лоток со строками без исхода (ADR-0032 п.5) — коммит отклонён.\n"
            "  Исход начинается маркером: ✅ закрыта · ⬆️ поднята · ✂️ снята · ➡️ перенесена.\n"
            "  Перенос однажды: перенесённая повторно строка становится карточкой либо снимается.\n"
        )
        for f in fails:
            sys.stderr.write(f"  {f}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
