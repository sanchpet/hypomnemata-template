#!/usr/bin/env python3
"""PostToolUse-страж: гейты ADR-0006/ADR-0013 независимо от инструмента записи (ADR-0034).

PreToolUse-гейты висят на `Write|Edit|MultiEdit` и потому слепы к bash-пути
(`cat > файл <<'EOF'`), которым агент в этом vault пишет файлы штатно. Они были
исправны и бездействовали — самая дорогая форма отказа, потому что молчание гейта
неотличимо от его прохождения.

Страж закрывает путь, а не правило: после любого пишущего тула он спрашивает git,
что в дереве появилось или изменилось, и прогоняет это через **те же самые**
`check-naming.sh` и `task-artifact-check.py`. Своей копии правил у него нет — две
копии разъедутся, и разъехавшийся гейт хуже отсутствующего.

Блокировать постфактум нельзя: файл уже записан. На bash-пути гейт превращается
из запрета в громкое уведомление — хуже блокировки и несравнимо лучше молчания.

Канал до модели — JSON `hookSpecificOutput.additionalContext` (голый stdout при
exit 0 до модели не доходит, проверено пробой). Любой отказ — тихий exit 0.
"""
import sys
import os
import json
import re
import hashlib
import subprocess
from pathlib import Path

# Чужие деревья и служебные зоны: имена там не наши, а объём подкосил бы цену прогона.
EXCLUDE_PREFIXES = (
    ".git/", ".obsidian/", ".repos/", ".resources/", ".principles/",
    # ADR-0006: вложения вне правила имён — имя блоба служебное и задаётся
    # инструментом, которым мы не управляем (Obsidian, Excalidraw).
    "80-kernel/attachments/",
    "node_modules/", ".venv/",
)
EXCLUDE_PARTS = ("/node_modules/", "/.venv/", "/__pycache__/", "/.git/", "/.principles/")

TASK_CARD = re.compile(r"^10-governance/6-tasks/T-\d+[^/]*\.md$")
# Закрытая карточка артефакта уже не обещает — гейт к ней неприменим.
TASK_INACTIVE = {"done", "closed", "later", "dropped"}


def card_status(path: Path):
    try:
        txt = path.read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.match(r"---\n(.*?)\n---", txt, re.S)
    if not m:
        return None
    s = re.search(r"^status:\s*(.*)$", m.group(1), re.M)
    return s.group(1).strip().strip("\"'").strip().lower() if s else None


def changed_files(root: str):
    """Пути, которые git видит новыми или изменёнными. `-z` — чтобы не разбирать
    кавычки, которыми git экранирует кириллицу (а негодные имена как раз такие);
    `-uall` — иначе новый каталог приходит одной строкой `dir/`, и файлов в нём не видно."""
    try:
        out = subprocess.run(
            ["git", "-C", root, "status", "--porcelain", "-z", "-uall"],
            capture_output=True, text=True, timeout=10,
        ).stdout
    except Exception:
        return []
    toks = out.split("\0")
    paths, i = [], 0
    while i < len(toks):
        rec = toks[i]
        i += 1
        if len(rec) < 4:
            continue
        xy, rel = rec[:2], rec[3:]
        if "R" in xy or "C" in xy:
            i += 1  # за переименованием следует прежнее имя — пропускаем
        if "D" in xy:
            continue
        paths.append(rel)
    return paths


def main():
    root = os.environ.get("CLAUDE_PROJECT_DIR")
    if not root:
        return 0
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    session = payload.get("session_id") or "nosess"

    candidates = []
    for rel in changed_files(root):
        if rel.startswith(EXCLUDE_PREFIXES) or any(p in "/" + rel for p in EXCLUDE_PARTS):
            continue
        p = Path(root) / rel
        if not p.is_file():
            continue
        candidates.append((rel, p))
    if not candidates:
        return 0

    # Марка по паре «путь + mtime»: файл, уже проверенный в этом виде, не
    # перепроверяется — иначе страж платил бы полную цену на каждый вызов тула.
    stamp_dir = Path(os.environ.get("TMPDIR", "/tmp")) / "hypomnemata-guard"
    try:
        stamp_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return 0

    fresh = []
    for rel, p in candidates:
        try:
            key = hashlib.sha1(f"{session}|{rel}|{p.stat().st_mtime_ns}".encode()).hexdigest()
        except OSError:
            continue
        stamp = stamp_dir / key
        if stamp.exists():
            continue
        try:
            stamp.touch()
        except OSError:
            continue
        fresh.append((rel, p))
    if not fresh:
        return 0

    hooks = Path(root) / ".claude" / "hooks"
    scripts = Path(root) / "80-kernel" / "scripts"
    violations = []

    # ADR-0006 — имена. Батч одним вызовом: правило живёт в check-naming.sh.
    try:
        r = subprocess.run(
            ["bash", str(hooks / "check-naming.sh")] + [str(p) for _, p in fresh],
            capture_output=True, text=True, timeout=20,
            env={**os.environ, "CLAUDE_PROJECT_DIR": root},
        )
        if r.returncode == 2:
            violations += [ln for ln in r.stderr.splitlines() if ln.strip()]
    except Exception:
        pass

    # ADR-0036 п.7 — рабочий продукт у задачи, ВЗЯТОЙ В ЮНИТ (условие внутри скрипта).
    cards = [
        str(p) for rel, p in fresh
        if TASK_CARD.match(rel)
        and "/archive/" not in "/" + rel
        and (card_status(p) or "") not in TASK_INACTIVE
    ]
    if cards:
        try:
            r = subprocess.run(
                [sys.executable, str(scripts / "task-artifact-check.py")] + cards,
                capture_output=True, text=True, timeout=20,
            )
            if r.returncode == 2:
                violations += [ln for ln in r.stderr.splitlines() if ln.strip()]
        except Exception:
            pass

    if not violations:
        return 0

    listed = "\n".join(f"  • {v}" for v in violations)
    msg = (
        "Страж записи (ADR-0034) — нарушения в только что изменённых файлах:\n"
        f"{listed}\n\n"
        "Файл уже записан: на bash-пути (`cat > … <<'EOF'`) PreToolUse-гейт не "
        "срабатывает, поэтому это уведомление, а не блокировка. Исправь сейчас — "
        "переименуй файл (`git mv`, если он уже под версией) либо заполни `artifact:`. "
        "Молча оставлять нельзя: гейт для того и заведён."
    )
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": msg,
    }}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # страж не роняет сессию ни при каких обстоятельствах
