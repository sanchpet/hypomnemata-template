#!/usr/bin/env python3
"""Детектор зеркал задач в приборе учёта времени (ADR-0033, кратность правлена ADR-0036 п.5).

Задача, **взятая в юнит**, обязана иметь в Super Productivity хотя бы одну работу —
иначе физическое время по ней списывать некуда (INV-15).

Кратность 1:N, а не 1:1. По ADR-0036 в приборе живут не задачи, а **работы**: работа
есть уточнённая задача (известно, когда и в каком порядке исполняется), и одна задача
может дать их несколько. Поэтому проверяется существование, а не соответствие.

Задачи вне юнита не проверяются вовсе: они ещё не запланированы, работ у них нет
по построению, и краснеть тут не на что.

Вход: список карточек берётся из vault сам; показания прибора подаются на stdin
СЫРЫМ ТЕКСТОМ — что угодно, лишь бы в нём встречались заголовки задач
(вывод `mcp__super-productivity__get_tasks`, JSON или нет). Скрипт в прибор не
ходит и его протокола не знает: он ищет в тексте метку `T-NNN`. Это и есть
развязка — смена формата ответа MCP детектор не ломает (ЭМОГССБ: эволюционируемость).

Связь карточка↔работа — по префиксу `T-NNN` в заголовке работы (переходно
принимаются и прежние `РП-NNN` / `WP-NNN`). Id задачи в
карточку не пишется: за карточками следит PostToolUse-хук, обратная запись дала
бы петлю.

Exit 0 — у всех задач юнита есть работы; exit 1 — есть задача без единой работы;
exit 2 — ошибка употребления (пустой stdin, нет каталога задач).

Пример:
    <вывод get_tasks> | 80-kernel/scripts/task-mirror-check.py

see 80-kernel/stele/ADR-0033-wp-mirrored-in-time-tracker.md · ADR-0036-task-as-atomic-card.md
"""
import sys
import re
import argparse
from pathlib import Path

# Петля закрыта либо работа снята — зеркало больше не нужно.
INACTIVE = {"done", "closed", "later", "dropped"}

# Границы обязательны: id задач SP — плотная буквенно-цифровая каша,
# без них «…wP7…» внутри id зачлось бы за зеркало РП-007 (ложное зелёное).
MARK = re.compile(r"(?<![0-9A-Za-zА-Яа-я])(?:РП|WP|T)[-\s]?0*(\d{1,4})(?![0-9A-Za-zА-Яа-я])",
                  re.IGNORECASE)
CARD = re.compile(r"^T-(\d+)", re.IGNORECASE)


def card_field(path, field):
    """Значение произвольного поля frontmatter; пустая строка — если нет."""
    try:
        txt = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    m = re.match(r"---\n(.*?)\n---", txt, re.S)
    if not m:
        return ""
    f = re.search(rf"^{field}:\s*(.*)$", m.group(1), re.M)
    return f.group(1).strip().strip("\"'").strip() if f else ""


def card_status(path):
    """Значение `status` из frontmatter; None — если frontmatter нет."""
    try:
        txt = path.read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.match(r"---\n(.*?)\n---", txt, re.S)
    if not m:
        return None
    s = re.search(r"^status:\s*(.*)$", m.group(1), re.M)
    return s.group(1).strip().strip("\"'").strip().lower() if s else None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", type=Path,
                    default=Path(__file__).resolve().parents[2],
                    help="корень vault (по умолчанию — выводится из пути скрипта)")
    args = ap.parse_args()

    task_dir = args.vault / "10-governance" / "6-tasks"
    if not task_dir.is_dir():
        sys.stderr.write(f"не найден каталог задач: {task_dir}\n")
        return 2

    raw = sys.stdin.read()
    if not raw.strip():
        sys.stderr.write(
            "stdin пуст — подай показания прибора: "
            "<вывод mcp__super-productivity__get_tasks> | task-mirror-check.py\n"
            "Пустой вход покрасил бы в красное всё подряд, это не находка.\n")
        return 2

    mirrored = {int(n) for n in MARK.findall(raw)}

    in_unit, missing, outside = [], [], 0
    for path in sorted(task_dir.glob("T-*.md")):
        m = CARD.match(path.name)
        if not m:
            continue
        status = card_status(path)
        if status in INACTIVE:
            continue
        # Проверяется только взятое в юнит: у незапланированной задачи работ нет законно.
        if not card_field(path, "unit"):
            outside += 1
            continue
        num = int(m.group(1))
        in_unit.append((num, path.name, status or "?"))
        if num not in mirrored:
            missing.append((num, path.name, status or "?"))

    print(f"Задач в юните: {len(in_unit)} · с работами в приборе: "
          f"{len(in_unit) - len(missing)} · без единой работы: {len(missing)} "
          f"· вне юнита (не проверялись): {outside}")
    if not missing:
        print("Зелено: у каждой задачи юнита есть хотя бы одна работа в приборе.")
        return 0

    print("\nНи одной работы в приборе (списывать физическое время некуда, INV-15):")
    for num, name, status in missing:
        print(f"  T-{num:03d}  [{status}]  {name}")
    print("\nЗавести: mcp__super-productivity__create_task, "
          "заголовок `T-NNN — <формулировка работы>`, "
          "project_id проекта-зеркала, time_estimate = бюджет работы в мс. "
          "Работ у задачи может быть несколько — заводится каждая.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
