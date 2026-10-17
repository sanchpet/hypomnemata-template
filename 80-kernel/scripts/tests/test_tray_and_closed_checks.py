#!/usr/bin/env python3
"""Tests for tray-outcome-check.py and closed-date-check.py.

Each detector is proven to go red on a bad fixture and green on a good one,
through the same entry point pre-commit uses (a subprocess with file args).
Run: python3 80-kernel/scripts/tests/test_tray_and_closed_checks.py (or pytest).
"""
import datetime
import importlib.util
import os
import subprocess
import sys
import tempfile

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAY = os.path.join(SCRIPTS, "tray-outcome-check.py")
CLOSED = os.path.join(SCRIPTS, "closed-date-check.py")
sys.path.insert(0, SCRIPTS)


def load(path):
    spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3].replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(script, root, *rel):
    return subprocess.run(
        [sys.executable, script, *rel], cwd=root, stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=10,
    )


def run_open_stdin(script, root):
    """No-arg run with stdin an open, never-written pipe: a stdin read would hang."""
    rfd, wfd = os.pipe()
    try:
        return subprocess.run([sys.executable, script], cwd=root, stdin=rfd,
                              capture_output=True, text=True, timeout=5)
    finally:
        os.close(rfd)
        os.close(wfd)


def git(root, *args):
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid",
         "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *args],
        cwd=root, check=True, capture_output=True, stdin=subprocess.DEVNULL,
    )


def repo(root, files):
    """A git repo whose HEAD holds `files` ({rel: text})."""
    git(root, "init", "-q")
    for rel, txt in files.items():
        write(root, rel, txt)
    git(root, "add", "-A")
    git(root, "commit", "-q", "--no-verify", "-m", "base")


def write(root, rel, txt):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(txt)
    return rel


TRAY_HEAD = """---
type: forreview
---

## Вынесено к разбору

| # | Что | Кем | Источник | Исход |
|---|-----|-----|----------|-------|
"""
TRAY_DRAINED = TRAY_HEAD + (
    "| 1 | вопрос со [[T-001-x|T-001]] | агент | `a.md:1` | ⬆️ поднята в [[T-001-x|T-001]] |\n"
    "| 2 | второй | владелец | разговор | ✂️ снята |\n"
    "| 3 | | | | — |\n"
    "\n## Дефекты\n\n| # | Дефект | Свидетельство | Исход |\n|---|---|---|---|\n"
    "| A | — | — | дефектов не дала |\n"
)
TRAY_OPEN = TRAY_HEAD + (
    "| 1 | закрытый | агент | `a.md:1` | ✅ закрыта |\n"
    "| 2 | открытый с [[x|y]] в предмете | агент | `b.md \\| c` | — |\n"
    "| 3 | без ячейки исхода | агент | `c.md` | |\n"
)


def test_tray_red_on_archived_tray_with_empty_outcome():
    with tempfile.TemporaryDirectory() as root:
        rel = write(root, "10-governance/7-plans/archive/2026-w01-w02-forreview.md", TRAY_OPEN)
        r = run(TRAY, root, rel)
        assert r.returncode == 1, r
        assert "#2 без исхода" in r.stderr and "#3 без исхода" in r.stderr, r.stderr
        assert "#1 " not in r.stderr, r.stderr


def test_tray_green_on_drained_archived_tray():
    with tempfile.TemporaryDirectory() as root:
        rel = write(root, "10-governance/7-plans/archive/2026-w01-w02-forreview.md", TRAY_DRAINED)
        r = run(TRAY, root, rel)
        assert r.returncode == 0, r.stderr


def test_tray_silent_on_review_tray_being_filled():
    with tempfile.TemporaryDirectory() as root:
        rel = write(root, "10-governance/7-plans/review/2026-w01-w02-forreview.md", TRAY_OPEN)
        assert run(TRAY, root, rel).returncode == 0


def test_no_args_does_not_read_stdin():
    with tempfile.TemporaryDirectory() as root:
        for script in (TRAY, CLOSED):
            assert run_open_stdin(script, root).returncode == 0, script


def test_tray_placeholder_outcomes_count_as_empty():
    mod = load(TRAY)
    for cell in ["**—**", "*—*", "<br>", "``", "<!-- -->", "?", "…", "TODO",
                 "~~✅ закрыта~~", "🔴 **без исхода** → [[w38\\|лоток W38]]"]:
        txt = TRAY_HEAD + f"| 1 | вопрос | я | x | {cell} |\n"
        assert mod.empty_outcomes(txt), cell
    txt = TRAY_HEAD + "| 1 | вопрос | я | x | ✅ закрыта: строка без исхода в W38 разобрана |\n"
    assert mod.empty_outcomes(txt) == []


def test_tray_header_variants_and_split_table():
    mod = load(TRAY)
    row = "| 1 | вопрос | я | x | — |\n"
    for head in ["| # | Что | Кем | Источник | **Исход** |", "| # | Что | Кем | Источник | Исход строки |",
                 "| # | Что | Кем | Источник | Исходы |", "| # | Что | Кем | Источник | Исход"]:
        assert mod.empty_outcomes(f"{head}\n|---|---|---|---|---|\n{row}"), head
    split = TRAY_HEAD + "| 1 | a | я | x | ✅ закрыта |\n\n| 2 | b | я | x | — |\n"
    assert [num for _, num, _ in mod.empty_outcomes(split)] == ["2"]
    prose = TRAY_HEAD + "| 1 | a | я | x | ✅ закрыта |\n\nтекст\n\n| 2 | b | я | x | — |\n"
    assert mod.empty_outcomes(prose) == []


def test_tray_archive_subfolder_is_checked():
    with tempfile.TemporaryDirectory() as root:
        rel = write(root, "10-governance/7-plans/archive/2026/2026-w01-forreview.md", TRAY_OPEN)
        assert run(TRAY, root, rel).returncode == 1


def test_tray_history_grandfathered_but_new_gaps_and_archiving_red():
    arch = "10-governance/7-plans/archive/2026-w01-w02-forreview.md"
    review = "10-governance/7-plans/review/2026-w03-w04-forreview.md"
    with tempfile.TemporaryDirectory() as root:
        repo(root, {arch: TRAY_OPEN, review: TRAY_OPEN})
        write(root, arch, TRAY_OPEN + "\nправка ссылки\n")
        assert run(TRAY, root, arch).returncode == 0
        r = run(TRAY, root, "--strict", arch)
        assert r.returncode == 1 and "#2 без исхода" in r.stderr, r
        write(root, arch, TRAY_OPEN.replace("✅ закрыта", "—"))
        r = run(TRAY, root, arch)
        assert r.returncode == 1 and "#1 без исхода" in r.stderr and "#2 " not in r.stderr, r
        moved = "10-governance/7-plans/archive/2026-w03-w04-forreview.md"
        git(root, "mv", review, moved)
        r = run(TRAY, root, moved)
        assert r.returncode == 1 and "#2 без исхода" in r.stderr, r


def test_tray_outcome_must_start_with_a_known_marker():
    mod = load(TRAY)
    for cell in ["⚙️ **частично, 05.09**: заведён скелет", "◐ **частично** — повестка правлена",
                 "↪ **перенесена** → лоток W38", "закрыта 03.10", "дефектов не дала",
                 "🔴 решено", "решено ✅"]:
        txt = TRAY_HEAD + f"| 1 | вопрос | я | x | {cell} |\n"
        assert mod.empty_outcomes(txt), cell
    for cell in ["✅ закрыта", "**⬆️ поднята** в [[T-1-x\\|T-1]]", "⬆ поднята", "✂️ снята — исход не записан",
                 "~~лишнее~~ ➡️ перенесена в лоток W02", "✅ снято прибором 20.09"]:
        txt = TRAY_HEAD + f"| 1 | вопрос | я | x | {cell} |\n"
        assert mod.empty_outcomes(txt) == [], cell


def test_tray_carried_over_only_once():
    mod = load(TRAY)
    again = TRAY_HEAD + "| 1 | вопрос | перенесена из лотка W01 | x | ➡️ перенесена в лоток W03 |\n"
    assert [(num, why) for _, num, why in mod.empty_outcomes(again)] == [("1", "перенесена повторно")]
    for txt in [TRAY_HEAD + "| 1 | вопрос | перенесена из лотка W01 | x | ⬆️ поднята в [[T-1-x\\|T-1]] |\n",
                TRAY_HEAD + "| 1 | вопрос | владелец 05.09 | x | ➡️ перенесена в лоток W03 |\n",
                TRAY_HEAD + "| 1 | перенесённый курс | владелец | x | ➡️ перенесена |\n"]:
        assert mod.empty_outcomes(txt) == [], txt
    with tempfile.TemporaryDirectory() as root:
        rel = write(root, "10-governance/7-plans/archive/2026-w03-forreview.md", again)
        r = run(TRAY, root, rel)
        assert r.returncode == 1 and "#1 перенесена повторно" in r.stderr, r


def test_tray_partial_outcome_red_through_cli():
    with tempfile.TemporaryDirectory() as root:
        rel = write(root, "10-governance/7-plans/archive/2026-w01-forreview.md",
                    TRAY_HEAD + "| 1 | вопрос | я | x | ⚙️ частично |\n")
        r = run(TRAY, root, rel)
        assert r.returncode == 1 and "#1 без исхода" in r.stderr, r
        write(root, rel, TRAY_HEAD + "| 1 | вопрос | я | x | ✂️ снята — исход не записан |\n")
        assert run(TRAY, root, rel).returncode == 0


def test_tray_wikilink_pipe_does_not_shift_outcome_column():
    mod = load(TRAY)
    assert mod.empty_outcomes(TRAY_DRAINED) == []
    assert [num for _, num, _ in mod.empty_outcomes(TRAY_OPEN)] == ["2", "3"]


def card(type_, status, closed=None, opened=None):
    lines = ["---", f"type: {type_}", f"status: {status}"]
    if opened:
        lines.append(f"opened: {opened}")
    if closed is not None:
        lines.append(f"closed: {closed}")
    return "\n".join(lines + ["---", "", "# card", ""])


TODAY = datetime.date(2026, 10, 4)


def test_closed_red_cases():
    mod = load(CLOSED)
    bad = {
        "missing": card("task", "done"),
        "empty": card("task", "dropped", closed=""),
        "not a date": card("task", "closed", closed="03.10.2026"),
        "impossible": card("task", "done", closed="2026-02-30"),
        "future": card("task", "done", closed="2026-10-05"),
        "before opened": card("task", "done", closed="2026-09-01", opened="2026-09-02"),
        "legacy kind": card("work-product", "closed"),
        "project": card("project", "merged"),
        "project with task word": card("project", "dropped"),
        "project with goal word": card("project", "achieved"),
    }
    for name, txt in bad.items():
        assert mod.check(txt, name, TODAY), name


def test_closed_green_cases():
    mod = load(CLOSED)
    good = {
        "today": card("task", "done", closed="2026-10-04", opened="2026-10-04"),
        "quoted with comment": card("task", "closed", closed='"2026-09-30"  # note'),
        "live task": card("task", "in-progress"),
        "live project": card("project", "active"),
        "other kind": card("dissatisfaction", "resolved"),
        "no frontmatter": "# just text\n",
    }
    for name, txt in good.items():
        assert mod.check(txt, name, TODAY) is None, (name, mod.check(txt, name, TODAY))


def test_closed_through_cli():
    with tempfile.TemporaryDirectory() as root:
        bad = write(root, "10-governance/6-tasks/T-001-a.md", card("task", "done"))
        good = write(root, "10-governance/6-tasks/T-002-b.md", card("task", "done", closed="2026-01-01"))
        r = run(CLOSED, root, bad, good)
        assert r.returncode == 1 and "T-001-a.md" in r.stderr and "T-002-b.md" not in r.stderr, r
        assert run(CLOSED, root, good).returncode == 0
        assert run(CLOSED, root).returncode == 0


def test_closed_history_grandfathered_but_new_closure_red():
    legacy = "10-governance/6-tasks/archive/T-001-legacy.md"
    live = "10-governance/6-tasks/T-002-live.md"
    dated = "10-governance/6-tasks/T-003-dated.md"
    with tempfile.TemporaryDirectory() as root:
        repo(root, {legacy: card("work-product", "done"), live: card("task", "in-progress"),
                    dated: card("task", "done", closed="2026-01-01")})
        write(root, legacy, card("task", "done") + "правка ссылки\n")
        assert run(CLOSED, root, legacy).returncode == 0
        assert run(CLOSED, root, "--strict", legacy).returncode == 1
        moved = "10-governance/6-tasks/archive/T-001-moved.md"
        git(root, "mv", legacy, moved)
        assert run(CLOSED, root, moved).returncode == 0
        write(root, live, card("task", "done"))
        r = run(CLOSED, root, live)
        assert r.returncode == 1 and "T-002-live.md" in r.stderr, r
        write(root, dated, card("task", "done"))
        assert run(CLOSED, root, dated).returncode == 1
        fresh = write(root, "10-governance/6-tasks/T-004-new.md", card("task", "done"))
        assert run(CLOSED, root, fresh).returncode == 1


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    for name, fn in tests:
        fn()
        print(f"ok  {name}")
    print(f"{len(tests)} passed")
