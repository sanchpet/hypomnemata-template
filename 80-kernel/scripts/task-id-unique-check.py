#!/usr/bin/env python3
"""Гейт уникальности номера задачи (INV-5).

Номер задачи присваивается чтением каталога, а параллельные сессии читают одно и то же
состояние: обе видят номер свободным и обе его берут. У автора это случилось дважды
за одну неделю. Правило «посмотри, свободен ли номер» уже действовало
и не сработало — потому что смотрят одновременно.

Гейт ловит коллизию в момент коммита, а не через неделю на ревизии активных задач.
Проверяется весь каталог, а не только staged-файлы: коллизия по определению
существует между двумя файлами, из которых staged может быть один.
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

TASK_DIR = Path("10-governance/6-tasks")
NAME_RE = re.compile(r"^T-(\d+)-")
ID_RE = re.compile(r"^id:\s*[Tt]-(\d+)\s*$", re.MULTILINE)


def main() -> int:
    by_number = defaultdict(list)
    mismatched = []

    for path in sorted(TASK_DIR.glob("T-*.md")):
        m = NAME_RE.match(path.name)
        if not m:
            continue
        number = m.group(1)
        by_number[number].append(path.name)

        id_match = ID_RE.search(path.read_text(encoding="utf-8"))
        if id_match and id_match.group(1) != number:
            mismatched.append((path.name, id_match.group(1)))

    problems = []

    for number, files in sorted(by_number.items()):
        if len(files) > 1:
            problems.append(
                f"  номер T-{number} занят дважды: " + " · ".join(files)
            )

    for name, id_number in mismatched:
        problems.append(
            f"  {name}: имя файла и поле id расходятся (id: T-{id_number})"
        )

    if problems:
        print("Коллизия номеров задач (ADR-0013/ADR-0036):")
        print("\n".join(problems))
        print(
            "\nПеренумеруй младший по времени заведения: "
            "переименуй файл, поправь `id:` и заголовок, почини ссылки."
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
