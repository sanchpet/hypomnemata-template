#!/usr/bin/env python3
"""Детектор разрыва цепочки (INV-14 / INV-17, ADR-0035, ADR-0040).

Безголовый эквивалент dataview-веток реестра: те живут только внутри Obsidian,
и потому не поддаются пробою (ADR-0034 — энфорсмент независим от инструмента).
Печатает только нарушения; молчит, когда цепочка цела. Отчёт, не гейт:
в хуки НЕ подключён, правка гейтов — на сессии стратегирования (INV-5).

Проверяется ТОЛЬКО ВНИЗ: младший называет старшего. Устремление без
неудовлетворённости, неудовлетворённость без проекта и проект без задач —
не нарушения, а свидетельство покоя (ADR-0035 п.6). Реестра целей нет:
проект и есть цель, его критерий — поле `criterion` (ADR-0040).
"""
import re, sys, pathlib, yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
G = ROOT / "10-governance"


def load(d):
    out = {}
    for p in (G / d).glob("*.md"):
        txt = p.read_text(encoding="utf-8")
        if not txt.startswith("---"):
            continue
        parts = re.split(r"(?m)^---\s*$", txt, maxsplit=2)
        if len(parts) < 3:
            continue
        try:
            fm = yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError:
            print(f"⚠️  {p.name}: frontmatter не парсится", file=sys.stderr)
            continue
        out[p.stem] = fm
    return out


def target(v):
    """Цель ссылки [[stem|display]] либо None для пустого значения."""
    if not v or (isinstance(v, list) and not v):
        return None
    if isinstance(v, list):
        v = v[0]
    m = re.search(r"\[\[([^\]|#]+)", str(v))
    return m.group(1).strip() if m else None


def main():
    dis = load("3-dissatisfactions")
    tasks = load("6-tasks")
    # Архивный проект существует: закрытая задача законно ссылается на него.
    root = G / "5-projects"
    cards = [*root.glob("P*/P*.md"), *root.glob("archive/P*/P*.md"), *root.glob("archive/P*.md")]
    projects = {p.stem: yaml.safe_load(
        re.split(r"(?m)^---\s*$", p.read_text(encoding="utf-8"), maxsplit=2)[1]) or {}
        for p in cards}

    flags = []

    for name, fm in sorted(dis.items()):
        if fm.get("type") != "dissatisfaction":
            continue
        if fm.get("status") == "active" and not target(fm.get("aspiration")):
            flags.append(("неудовлетворённость без устремления", name))

    for name, fm in sorted(projects.items()):
        if fm.get("type") != "project" or fm.get("status") != "active":
            continue
        if not (target(fm.get("dissatisfaction")) or target(fm.get("aspiration"))):
            flags.append(("проект без родителя", name))

    for name, fm in sorted(tasks.items()):
        if fm.get("type") != "task":      # backlog.md и прочие списки — не карточки
            continue
        proj = target(fm.get("project"))
        if not proj:
            flags.append(("задача без проекта", name))
            continue
        if fm.get("unit"):
            pfm = projects.get(proj)
            if pfm is None:
                flags.append(("задача ссылается на несуществующий проект", f"{name} → {proj}"))
            # Закрытая задача задним числом не перепроверяется: правило ADR-0040
            # смотрит вперёд, а юниты до него брались в проекты по полю `goal`.
            elif fm.get("status") in ("done", "closed", "dropped"):
                continue
            elif not pfm.get("criterion"):
                flags.append(("время выделено проекту без критерия", f"{name} → {proj}"))

    if not flags:
        print("✅ цепочка цела: разрывов нет")
        return 0
    print(f"🔴 разрывов цепочки: {len(flags)}")
    for kind, what in flags:
        print(f"  • {kind}: {what}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
