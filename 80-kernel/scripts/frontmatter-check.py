#!/usr/bin/env python3
"""Frontmatter-гейт Hypomnemata (pre-commit hook). Проверяет заметки vault:
  1) YAML-валидность frontmatter — ловит миграционные осколки (кавычки в кавычках,
     висячие двоеточия и пр.), которые Obsidian помечает «invalid properties».
  2) status-схема по ADR-0012 — для родов (`type`), где статус определён enum-ом
     (контент / РП / ADR). Прочие роды (governance / системные) ADR-0012 status-ом
     НЕ enum-ирует → проверяется только валидность (не выдумываем правил).

Вход: имена файлов аргументами (pre-commit передаёт staged-файлы). Только .md.
Exit 0 — чисто; exit 1 — есть нарушения (с перечнем в stderr).
См. ADR-0012, ADR-0019.
pyyaml — через pre-commit (language: python, additional_dependencies).
"""
import re
import sys

import yaml

CONTENT = ["later", "in-progress", "processed", "incubating", "done"]

# type → допустимые status. Рода нет в карте → status не проверяется.
STATUS = {
    "note": CONTENT, "learn-note": CONTENT, "journal": CONTENT, "quote": CONTENT,
    "book": CONTENT, "course": CONTENT, "guide": CONTENT,
    "source": CONTENT + ["active"],
    # ADR-0036: род «work-product» переименован в «task»; статус `dropped` внесён —
    # его употребляют хуки и детекторы.
    "task": ["in-progress", "blocked", "done", "later", "closed", "dropped"],
    # ADR-0040: реестр целей закрыт; `merged` — цель, слитая с проектом.
    "goal": ["active", "achieved", "withdrawn", "merged"],
    "adr": ["proposed", "accepted", "withdrawn"],  # + superseded* (префикс)
}


def frontmatter(txt):
    """Содержимое YAML-блока между ведущими '---' и следующим '---' (или None)."""
    if not txt.startswith("---"):
        return None
    parts = re.split(r"(?m)^---\s*$", txt, maxsplit=2)
    return parts[1] if len(parts) >= 3 else None


def main():
    fails = []
    for path in sys.argv[1:]:
        if not path.endswith(".md"):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                txt = f.read()
        except OSError:
            continue

        fm = frontmatter(txt)
        if fm is None:
            continue
        try:
            data = yaml.safe_load(fm) or {}
        except yaml.YAMLError as e:
            msg = str(e).splitlines()[0]
            fails.append(f"{path}: невалидный YAML frontmatter — {msg}")
            continue
        if not isinstance(data, dict):
            continue

        type_, status = data.get("type"), data.get("status")
        if type_ is None or status is None:
            continue
        allowed = STATUS.get(type_)
        if allowed is None:                          # род без status-схемы — только валидность
            continue

        ok = status in allowed or (type_ == "adr" and str(status).startswith("superseded"))
        if not ok:
            hint = ", ".join(allowed) + (", superseded*" if type_ == "adr" else "")
            fails.append(
                f"{path}: status '{status}' недопустим для type '{type_}' (ADR-0012). Допустимо: {hint}"
            )

    if fails:
        sys.stderr.write("✗ Frontmatter-гейт (ADR-0012) — коммит отклонён:\n")
        for f in fails:
            sys.stderr.write(f"  {f}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
