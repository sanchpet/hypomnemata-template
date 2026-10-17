#!/usr/bin/env python3
"""Гейт даты закрытия (pre-commit hook).

Карточка задачи либо проекта в терминальном статусе обязана нести `closed:` —
дату `YYYY-MM-DD`, не из будущего и не раньше `opened:`, если тот задан. Без даты
закрытие не подтверждается ничем: свод периода не знает, в какой период оно легло.

Терминальные статусы взяты из реестров: задача (`task`, исторический род
`work-product`) — `done` · `closed` · `dropped` (ADR-0012, frontmatter-check.py);
проект — `done` · `archived` · `merged` с карточек (enum в ADR нет) плюс финалы
задач и целей, чтобы перенесённое из них слово не проходило молча.
Прочие роды гейт не трогает.

Гейт ловит акт закрытия, а не касание: карточка, терминальная уже в HEAD и уже
тогда без `closed:`, — история, её правка не блокируется.
Краснеют новое закрытие без даты, снятая дата и дата неверная. `--strict`
снимает поблажку для сверки всего реестра.

Вход: имена файлов аргументами (pre-commit передаёт staged-файлы); без
аргументов — выход 0 без чтения stdin. Exit 0 — чисто; exit 1 — нарушения.
"""
import datetime
import re
import sys

import hookgit

TASK_FINAL = {"done", "closed", "dropped"}
TERMINAL = {
    "task": TASK_FINAL,
    "work-product": TASK_FINAL,
    "project": TASK_FINAL | {"archived", "merged", "achieved", "withdrawn", "cancelled"},
}
ISO = re.compile(r"\d{4}-\d{2}-\d{2}")


def field(fm, name):
    m = re.search(rf"^{name}:[ \t]*(.*)$", fm, re.M)
    if not m:
        return ""
    return re.sub(r"\s+#.*$", "", m.group(1)).strip().strip("\"'").strip()


def parse(value):
    if not ISO.fullmatch(value):
        return None
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        return None


def frontmatter(txt):
    m = re.match(r"---\n(.*?)\n---", txt or "", re.S)
    return m.group(1) if m else None


def undated_closure(txt):
    """Карточка терминальна и не несёт `closed:`."""
    fm = frontmatter(txt)
    return (fm is not None and field(fm, "status") in TERMINAL.get(field(fm, "type"), ())
            and not field(fm, "closed"))


def check(txt, label, today, head=None):
    """`head` — текст карточки в HEAD; закрытие без даты, бывшее там же, — история."""
    fm = frontmatter(txt)
    if fm is None:
        return None
    type_, status = field(fm, "type"), field(fm, "status")
    if status not in TERMINAL.get(type_, ()):
        return None

    raw = field(fm, "closed")
    if not raw:
        if head is not None and undated_closure(head):
            return None
        return f"{label}: {type_} в статусе `{status}` без `closed:` — впиши дату закрытия YYYY-MM-DD"
    closed = parse(raw)
    if closed is None:
        return f"{label}: `closed: {raw}` — не дата YYYY-MM-DD"
    if closed > today:
        return f"{label}: `closed: {raw}` в будущем (сегодня {today.isoformat()})"
    opened = parse(field(fm, "opened"))
    if opened and closed < opened:
        return f"{label}: `closed: {raw}` раньше `opened: {opened.isoformat()}`"
    return None


def main(args, today=None):
    today = today or datetime.date.today()
    strict = "--strict" in args
    paths = [a for a in args if a != "--strict"]
    renames = {} if strict or not paths else hookgit.staged_renames()
    fails = []
    for path in paths:
        try:
            with open(path, encoding="utf-8") as f:
                txt = f.read()
        except OSError as e:
            fails.append(f"{path}: не прочитан ({e})")
            continue
        head = None if strict else hookgit.head_text(hookgit.head_source(path, renames))
        err = check(txt, path, today, head)
        if err:
            fails.append(err)
    if fails:
        sys.stderr.write("✗ Закрытая карточка без верной даты `closed:` — коммит отклонён:\n")
        for f in fails:
            sys.stderr.write(f"  {f}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
