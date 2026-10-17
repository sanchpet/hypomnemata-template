#!/usr/bin/env python3
"""Week time from Super Productivity into 10-governance/7-plans/current/week-time.md (optional).

The home page cannot read SP, so this writes the current ISO week's tracked time into the vault:
per day and in total, in minutes — tracked, role (the employment project), personal, the invested
tag, and the tag outside role. Run it on a schedule of your choice (launchd, cron, systemd timer);
a machine without SP gets nothing and no error.

Settings come from the environment first, then from 80-kernel/config.md lines of the form
`key: value` (markdown emphasis around them is tolerated):
  timezone         IANA zone, e.g. Europe/Berlin         (env WEEK_TIME_TZ; default: system zone)
  sp_invested_tag  SP tag id of the invested-time tag    (env WEEK_TIME_INVESTED_TAG)
  sp_role_prefix   "title prefix" of the role project(s) (env WEEK_TIME_ROLE_PREFIX, quoted in config)
  SP_BACKUPS       env only: SP backup directory         (default: the macOS location)
An unset tag or prefix counts that column as 0 and says so on stderr.

Only leaf tasks count: SP keeps a parent's time as the sum of its subtasks. A subtask inherits
its parent's tags and project, because the tag usually sits on the parent alone.
Stdlib only and 3.9-compatible: a scheduler may fall back to the system python3.
"""
import datetime
import glob
import json
import os
import re
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
CONFIG = os.path.join(ROOT, "80-kernel", "config.md")
OUT = os.path.join(ROOT, "10-governance", "7-plans", "current", "week-time.md")
BACKUPS = os.path.expanduser(os.environ.get(
    "SP_BACKUPS", "~/Library/Application Support/superProductivity/backups"))
# A backup caught mid-write parses as truncated JSON; walk back a few rather than give up.
MAX_CANDIDATES = 5
KINDS = ("tracked", "role", "personal", "invested", "invested_outside_role")
WD = ("пн", "вт", "ср", "чт", "пт", "сб", "вс")
# Lines that change with every backup; a file differing only in them is not rewritten.
STAMP = re.compile(r"^(source_backup:|as_of:|По данным на ).*$", re.M)


def setting(env, pattern):
    if os.environ.get(env):
        return os.environ[env]
    try:
        with open(CONFIG, encoding="utf-8") as fh:
            m = re.search(pattern, fh.read())
    except OSError:
        return ""
    return m.group(1).strip() if m else ""


def zone():
    name = setting("WEEK_TIME_TZ", r"\btimezone:\s*`?([A-Za-z_]+(?:/[A-Za-z0-9_+-]+)+)")
    if name:
        try:
            return ZoneInfo(name)
        except ZoneInfoNotFoundError:
            print("week-time: unknown timezone %r, using the system zone" % name, file=sys.stderr)
    return datetime.datetime.now().astimezone().tzinfo


TZ = zone()
INVESTED_TAG = setting("WEEK_TIME_INVESTED_TAG", r"\bsp_invested_tag:\s*`?([A-Za-z0-9_-]+)")
ROLE_PREFIX = setting("WEEK_TIME_ROLE_PREFIX", r"\bsp_role_prefix:\s*\"([^\"]+)\"")


def load():
    files = sorted(glob.glob(os.path.join(BACKUPS, "*.json")), key=os.path.getmtime, reverse=True)
    for path in files[:MAX_CANDIDATES]:
        try:
            with open(path, encoding="utf-8") as fh:
                return path, json.load(fh)
        except (ValueError, OSError):
            continue
    raise SystemExit("week-time: no parseable backup among the newest %d in %s" % (MAX_CANDIDATES, BACKUPS))


def tasks(data):
    out = {}
    for store in (data, data.get("archiveYoung") or {}, data.get("archiveOld") or {}):
        for tid, t in ((store.get("task") or {}).get("entities") or {}).items():
            out.setdefault(tid, t)
    return out


def week_minutes(data, days):
    projects = (data.get("project") or {}).get("entities") or {}
    role = set()
    if ROLE_PREFIX:
        role = {pid for pid, p in projects.items() if str(p.get("title", "")).startswith(ROLE_PREFIX)}
        if not role:
            print("week-time: no SP project titled '%s…'; role counted as 0" % ROLE_PREFIX, file=sys.stderr)
    else:
        print("week-time: sp_role_prefix not set; role counted as 0", file=sys.stderr)
    if not INVESTED_TAG:
        print("week-time: sp_invested_tag not set; invested counted as 0", file=sys.stderr)
    elif INVESTED_TAG not in ((data.get("tag") or {}).get("entities") or {}):
        print("week-time: tag %s not found in SP" % INVESTED_TAG, file=sys.stderr)

    ms = {k: [0] * len(days) for k in ("tracked", "role", "invested", "invested_role")}
    all_tasks = tasks(data)
    for t in all_tasks.values():
        if t.get("subTaskIds"):
            continue
        parent = all_tasks.get(t.get("parentId")) or {}
        in_role = (t.get("projectId") or parent.get("projectId")) in role
        invested = bool(INVESTED_TAG) and INVESTED_TAG in set(t.get("tagIds") or []) | set(parent.get("tagIds") or [])
        spent = t.get("timeSpentOnDay") or {}
        for i, day in enumerate(days):
            v = spent.get(day) or 0
            ms["tracked"][i] += v
            ms["role"][i] += v if in_role else 0
            ms["invested"][i] += v if invested else 0
            ms["invested_role"][i] += v if invested and in_role else 0

    m = lambda x: int(round(x / 60000.0))
    out = {
        "tracked": [m(x) for x in ms["tracked"]],
        "role": [m(x) for x in ms["role"]],
        "invested": [m(x) for x in ms["invested"]],
        "invested_outside_role": [m(a - b) for a, b in zip(ms["invested"], ms["invested_role"])],
    }
    out["personal"] = [a - b for a, b in zip(out["tracked"], out["role"])]
    return out


def hm(minutes):
    return "%d:%02d" % divmod(minutes, 60)


def render(week, stamp, as_of, days, by_day):
    total = {k: sum(by_day[k]) for k in KINDS}
    fm = ["---", "type: week-time", 'week: "%s"' % week, 'aliases: ["Время недели %s"]' % week,
          'source_backup: "%s"' % stamp, 'as_of: "%s"' % as_of]
    fm += ["%s: %d" % (k, total[k]) for k in KINDS]
    fm += ["%s_by_day: [%s]" % (k, ", ".join(str(x) for x in by_day[k])) for k in KINDS]
    fm.append("---")
    rows = ["| %s %s.%s | %s |" % (WD[i], d[8:10], d[5:7], " | ".join(hm(by_day[k][i]) for k in KINDS))
            for i, d in enumerate(days)]
    rows.append("| **Неделя** | %s |" % " | ".join("**%s**" % hm(total[k]) for k in KINDS))
    body = [
        "",
        "# Время недели %s" % week,
        "",
        "> Генерируется `80-kernel/scripts/week-time.py` из бэкапа Super Productivity по расписанию. "
        "Руками не править: следующий прогон перезапишет.",
        "",
        "По данным на %s (бэкап `%s`). Считаются только листья задач; подзадача наследует тег и проект родителя." % (as_of, stamp),
        "",
        "| День | Учтено | Роль | Личное | Инвестированное | Инвестированное вне роли |",
        "|---|---|---|---|---|---|",
    ] + rows + [
        "",
        "Учтено = роль + личное. Роль — проекты прибора с префиксом `sp_role_prefix`. "
        "Инвестированное вне роли — тег `sp_invested_tag` за вычетом задач роли.",
        "",
    ]
    return "\n".join(fm + body)


def main():
    if not os.path.isdir(BACKUPS):
        return
    path, data = load()
    stamp = os.path.splitext(os.path.basename(path))[0]
    sm = re.match(r"(\d{4}-\d{2}-\d{2})_(\d{2})(\d{2})", stamp)
    as_of = "%s %s:%s" % sm.groups() if sm else datetime.datetime.fromtimestamp(os.path.getmtime(path), TZ).strftime("%Y-%m-%d %H:%M")

    today = datetime.datetime.now(TZ).date()
    monday = today - datetime.timedelta(days=today.weekday())
    days = [(monday + datetime.timedelta(days=i)).isoformat() for i in range(7)]
    year, week_no, _ = today.isocalendar()
    week = "%d-W%02d" % (year, week_no)

    text = render(week, stamp, as_of, days, week_minutes(data, days))
    out = os.path.normpath(OUT)
    if not os.path.isdir(os.path.dirname(out)):
        return
    try:
        with open(out, encoding="utf-8") as fh:
            if STAMP.sub("", fh.read()) == STAMP.sub("", text):
                return
    except FileNotFoundError:
        pass
    tmp = out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, out)


if __name__ == "__main__":
    main()
