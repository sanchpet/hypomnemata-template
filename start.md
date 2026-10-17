---
aliases: [Старт, Start]
---

```dataviewjs
const el = this.container.createEl("b");
const tick = () => el.textContent = window.moment().format("ddd D MMM HH:mm");
tick();
const id = setInterval(tick, 1000);
this.component.register(() => clearInterval(id));
```

# Спринт → юнит → день

```dataviewjs
const DIR = "10-governance/7-plans/current";
const today = window.moment().format("YYYY-MM-DD");
const ymd = v => v?.toFormat ? v.toFormat("yyyy-MM-dd") : String(v ?? "").slice(0, 10);
const at = s => { const [y, m, d] = s.split("-").map(Number); return new Date(y, m - 1, d); };
const iso = d => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const shift = (s, n) => { const d = at(s); d.setDate(d.getDate() + n); return iso(d); };
const span = (a, b) => Math.round((at(b) - at(a)) / 864e5);
const dm = s => `${s.slice(8, 10)}.${s.slice(5, 7)}`;
const WD = ["вс", "пн", "вт", "ср", "чт", "пт", "сб"];
const monday = (y, w) => { const j4 = new Date(y, 0, 4); j4.setDate(4 - (j4.getDay() + 6) % 7 + (w - 1) * 7); return iso(j4); };
const isoWeek = s => {
  const d = at(s); d.setDate(d.getDate() + 3 - (d.getDay() + 6) % 7);
  const y = d.getFullYear();
  return `${y}-W${String(1 + Math.round((d - at(monday(y, 1))) / 6048e5)).padStart(2, "0")}`;
};

// The current plan of a kind is the latest that has started, else the nearest one about to start,
// so the page turns over with the next unit or sprint without naming files.
const plans = dv.pages(`"${DIR}"`).array();
const pick = type => {
  const xs = plans.filter(p => p.type === type && ymd(p.valid_from)).sort((a, b) => ymd(a.valid_from).localeCompare(ymd(b.valid_from)));
  return xs.filter(p => ymd(p.valid_from) <= today).pop() ?? xs[0] ?? null;
};
const sprint = pick("sprintplan"), unit = pick("unitplan");
const days = plans.filter(p => p.type === "dayplan").sort((a, b) => ymd(a.date).localeCompare(ymd(b.date)));
const day = days.find(p => ymd(p.date) === today) ?? null;
const archive = dv.pages('"10-governance/7-plans/archive"').array();
// /close moves the day's plan to archive, so an evening page must tell "closed" from "not opened".
const closed = day ? null : archive.find(p => p.type === "dayplan" && ymd(p.date) === today) ?? null;
// Names come from file names: Dataview may read a bare "2026-W40" in frontmatter as a date.
const named = (p, kind) => p?.file.name.replace(new RegExp(`-${kind}$`), "") ?? "";
const read = async p => p ? await app.vault.cachedRead(app.vault.getAbstractFileByPath(p.file.path)) : "";
const [sprintTxt, unitTxt, dayTxt] = [await read(sprint), await read(unit), await read(day)];
// Dataview clears the container before the await; a re-render would otherwise stack on the previous one.
this.container.innerHTML = "";

const section = (txt, name) => txt.match(new RegExp(`##\\s*${name}[^\\n]*\\n([\\s\\S]*?)(?=\\n##\\s|$)`))?.[1] ?? "";
const table = md => {
  const rows = md.split("\n").filter(l => l.trim().startsWith("|"))
    .map(l => l.trim().replace(/^\|/, "").replace(/(?<!\\)\|$/, "").split(/(?<!\\)\|/).map(c => c.trim()))
    .filter(r => !r.every(c => /^:?-+:?$/.test(c)));
  const [head, ...body] = rows;
  return head ? body.map(r => Object.fromEntries(head.map((k, i) => [k.toLowerCase(), r[i] ?? ""]))) : [];
};
const col = (row, key) => Object.entries(row).find(([k]) => k.includes(key))?.[1] ?? "";
const LINK = /\[\[([^\]|#\\]+)(?:#[^\]|\\]*)?(?:\\?\|([^\]]+))?\]\]/g;
const targets = s => [...s.matchAll(LINK)].map(m => m[1].trim());
const plain = s => s.replace(LINK, (_, t, a) => a ?? t).replace(/\*\*|`/g, "").trim();
const page = name => dv.page(name) ?? null;
const base = l => String(l?.path ?? l ?? "").split("/").pop().replace(/\.md$/, "").replace(/^\[\[|\]\]$/g, "").split("|")[0];

const h = (parent, tag, css, text) => {
  const e = parent.appendChild(document.createElement(tag));
  e.style.cssText = css;
  if (text != null) e.textContent = text;
  return e;
};
const link = (e, target, src = "") => {
  e.style.cursor = "pointer";
  e.addEventListener("click", ev => app.workspace.openLinkText(target, src, ev.metaKey || ev.ctrlKey));
  e.addEventListener("mouseover", ev => app.workspace.trigger("hover-link", {
    event: ev, source: "preview", hoverParent: this.container, targetEl: e, linktext: target, sourcePath: src,
  }));
  return e;
};
// A table cell keeps its links clickable and its bold; the rest of the markdown is dropped.
const rich = (parent, s, src) => {
  let bold = false, i = 0;
  const text = t => t.replace(/`/g, "").split("**").forEach((part, k) => {
    if (k) bold = !bold;
    if (part) bold ? h(parent, "b", "font-weight:600;", part) : parent.append(part);
  });
  for (const m of s.matchAll(LINK)) {
    text(s.slice(i, m.index));
    link(h(parent, "span", `color:var(--text-normal);${bold ? "font-weight:600;" : ""}border-bottom:1px dotted var(--text-faint);`, (m[2] ?? m[1]).trim()), m[1].trim(), src);
    i = m.index + m[0].length;
  }
  text(s.slice(i));
  return parent;
};

// Three in a row or one in a column: a 2 + 1 wrap would break the 3/3/3 shape the page exists to show.
const grid = () => {
  const g = h(this.container, "div", "display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;");
  new ResizeObserver(() => { g.style.gridTemplateColumns = g.clientWidth < 3 * 166 + 2 * 10 ? "minmax(0,1fr)" : "repeat(3,minmax(0,1fr))"; }).observe(g);
  return g;
};
const card = (parent, color, dashed) => h(parent, "div", `display:flex;flex-direction:column;gap:5px;min-width:0;padding:8px 10px;border-radius:6px;line-height:1.35;color:var(--text-normal);background:var(--background-secondary);border:1px solid var(--background-modifier-border);border-left:3px ${dashed ? "dashed" : "solid"} ${color};`);
const dot = color => `display:inline-block;flex:none;width:7px;height:7px;border-radius:50%;background:${color};`;
const ring = `${dot("transparent")}box-shadow:inset 0 0 0 1.5px var(--text-faint);`;
const muted = n => `font-size:13px;color:var(--text-muted);display:-webkit-box;-webkit-line-clamp:${n};-webkit-box-orient:vertical;overflow:hidden;`;
// The thread wraps rather than truncates: its far end, the project, is the point of the line.
const chip = "display:flex;align-items:flex-start;gap:6px;margin-top:auto;padding-top:3px;font-size:12px;color:var(--text-muted);min-width:0;";
const pin = "margin-top:5px;";
const badge = "padding:0 5px;border:1px solid var(--background-modifier-border);border-radius:4px;font-size:11.5px;color:var(--text-muted);white-space:nowrap;";
const label = (first, title, plan, note) => {
  const e = h(this.container, "div", `display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 8px;margin:${first ? 4 : 18}px 0 6px;font-size:13px;color:var(--text-muted);`);
  h(e, "span", "font-weight:600;", title);
  if (plan) link(h(e, "span", "border-bottom:1px dotted var(--text-faint);", plan.label), plan.path);
  if (note) h(e, "span", "color:var(--text-faint);", note);
  return e;
};
const empty = text => h(this.container, "div", "padding:8px 10px;border:1px dashed var(--background-modifier-border);border-radius:6px;font-size:13px;color:var(--text-muted);", text);
// Where a plan stands in its own span: "неделя 1 из 12", or how soon it opens.
const progress = (p, unitName, unitDays) => {
  const from = ymd(p.valid_from), w = [p.weeks ?? []].flat()
    .map(x => (x?.toFormat ? x.toFormat("kkkk-'W'WW") : String(x)).match(/(\d{4})-W(\d+)/)).filter(Boolean);
  const to = w.length ? shift(monday(+w.at(-1)[1], +w.at(-1)[2]), 6) : null;
  const range = `${dm(from)}–${to ? dm(to) : "…"}`;
  if (today < from) return `${range} · начнётся через ${span(today, from)} дн.`;
  if (to && today > to) return `${range} · срок вышел ${dm(to)}`;
  const n = span(from, today), total = to ? span(from, to) + 1 : null;
  return `${range} · ${unitName} ${Math.floor(n / unitDays) + 1}${total ? ` из ${Math.ceil(total / unitDays)}` : ""}`;
};

// Each sprint goal owns a hue; unit results and day works inherit it through their project, which draws the thread.
// Green is left out: on the self-model it marks the sprint itself.
const HUES = ["var(--color-blue)", "var(--color-orange)", "var(--color-purple)"];
const goals = table(section(sprintTxt, "Три проекта-цели")).map((r, i) => {
  const cell = col(r, "проект"), name = targets(cell)[0] ?? "";
  return { r, i, name, p: page(name), color: HUES[i % HUES.length], title: cell.match(/\*\*(.+?)\*\*/)?.[1] ?? plain(cell) };
});
const goalOf = name => goals.find(g => g.name === name) ?? null;
// The role is a sprint goal kept outside the ranked three; the plan names it in its «Роль» paragraph.
const role = targets(sprintTxt.match(/^\*\*Роль[^\n]*/m)?.[0] ?? "").find(t => page(t)?.type === "project") ?? null;
const ROLE = "var(--text-muted)";
const hue = name => goalOf(name)?.color ?? (name && name === role ? ROLE : "var(--text-faint)");
const pid = name => page(name)?.id ?? name;

const results = table(section(unitTxt, "Три главных результата")).map((r, i) => ({ r, i, proj: targets(col(r, "проект"))[0] ?? "" }));
// A task serves the result its row in "Задачи юнита" names; a background task serves only its project.
const served = new Map(table(section(unitTxt, "Задачи юнита")).flatMap(r => {
  const n = parseInt(col(r, "результат"));
  return targets(col(r, "задача")).map(t => [t, Number.isFinite(n) ? n : null]);
}));

// Sprint
label(true, sprint ? `Спринт ${named(sprint, "sprintplan")}` : "Спринт", sprint && { label: "план", path: sprint.file.path }, sprint && progress(sprint, "неделя", 7));
if (!sprint) empty("SprintPlan в plans/current не найден — спринт не открыт.");
else if (!goals.length) empty("В плане спринта нет таблицы «Три проекта-цели спринта».");
else {
  const g = grid();
  goals.forEach(({ r, i, name, p, color, title }) => {
    const c = card(g, color);
    const head = h(c, "div", "display:flex;align-items:baseline;gap:6px;font-size:12px;color:var(--text-muted);");
    h(head, "span", `${dot(color)}align-self:center;`);
    h(head, "span", "white-space:nowrap;", `цель ${plain(r[""] ?? "") || i + 1} · ${pid(name)}`);
    const budget = plain(col(r, "бюджет"));
    if (budget) h(head, "span", `${badge}margin-left:auto;`, `${budget} ч`);
    link(h(c, "div", "font-size:13.5px;font-weight:600;", title), name, sprint.file.path).title = p?.criterion ?? title;
    const crit = col(r, "критерий");
    if (crit) rich(h(c, "div", muted(3)), crit, sprint.file.path).title = plain(crit);
    const mine = results.filter(x => x.proj === name).map(x => `результат ${plain(x.r[""] ?? "") || x.i + 1}`);
    h(h(c, "div", `${chip}${mine.length ? "" : "color:var(--text-faint);"}`), "span", "min-width:0;", mine.length ? `↓ в юните: ${mine.join(", ")}` : "↓ в этом юните результата нет");
  });
}

// Unit
label(false, unit ? `Юнит ${named(unit, "unitplan")}` : "Юнит", unit && { label: "план", path: unit.file.path }, unit && progress(unit, "день", 1));
if (!unit) empty("UnitPlan в plans/current не найден — юнит не открыт.");
else if (!results.length) empty("В плане юнита нет таблицы «Три главных результата».");
else {
  const g = grid();
  results.forEach(({ r, i, proj }) => {
    const goal = goalOf(proj), mine = goal || proj === role, color = hue(proj);
    const c = card(g, color, !mine);
    h(c, "div", "font-size:12px;color:var(--text-muted);", `результат ${plain(r[""] ?? "") || i + 1}`);
    rich(h(c, "div", "font-size:13.5px;"), col(r, "результат"), unit.file.path);
    const check = col(r, "чем проверяется");
    if (check) rich(h(c, "div", muted(3)), check, unit.file.path).title = plain(check);
    const up = h(c, "div", chip);
    h(up, "span", (mine ? dot(color) : ring) + pin);
    if (proj) link(h(up, "span", "min-width:0;", `↑ ${pid(proj)} · ${goal ? `цель ${goal.i + 1}` : mine ? "ролевая цель" : "вне трёх целей спринта"}`), proj, unit.file.path);
    else h(up, "span", "", "↑ проект не указан");
  });
}

// Day
const wd = WD[at(today).getDay()];
label(false, `День · ${wd} ${dm(today)}`, (day ?? closed) && { label: closed ? "план дня в архиве" : "план дня", path: (day ?? closed).file.path });
if (!day) {
  const e = empty(closed ? `День ${wd} ${dm(today)} закрыт: план ушёл в архив.` : `План дня на ${wd} ${dm(today)} ещё не создан — запусти /open.`);
  const refs = (lead, xs, tail) => {
    if (!xs.length) return;
    e.append(lead);
    xs.forEach((p, k) => { if (k) e.append(", "); link(h(e, "span", "border-bottom:1px dotted var(--text-faint);", dm(ymd(p.date))), p.file.path); });
    e.append(tail);
  };
  refs(" В plans/current остались планы на ", days.filter(p => ymd(p.date) < today), " — те дни не закрыты.");
  refs(" Уже готов план на ", days.filter(p => ymd(p.date) > today), ".");
} else {
  const works = table(section(dayTxt, "Работы дня"));
  if (!works.length) empty("В плане дня нет таблицы «Работы дня».");
  const g = grid();
  works.forEach(r => {
    const taskCell = col(r, "задача");
    const linked = targets(taskCell).map(page);
    const task = linked.find(t => t?.type === "task") ?? null;
    const own = task ? null : linked.find(p => p?.type === "project") ?? null;
    const proj = task ? base([task.project ?? []].flat()[0]) : own?.file.name ?? "";
    const n = task ? served.get(task.file.name) : null, goal = goalOf(proj), mine = goal || (proj && proj === role);
    const c = card(g, proj ? hue(proj) : "var(--text-faint)", !mine);
    const head = h(c, "div", "font-size:13.5px;");
    const flag = plain(r["🚦"] ?? "");
    if (flag) h(head, "span", "margin-right:5px;", flag);
    rich(h(head, "span", "font-weight:600;"), col(r, "работа"), day.file.path);
    const product = col(r, "продукт");
    if (product) rich(h(c, "div", muted(2)), product, day.file.path).title = plain(product);
    // The chip names one task; a second link, a remainder note or an extra column stays visible here.
    const extra = Object.entries(r).filter(([k, v]) => v && k && k !== "🚦" && !/работа|задача|продукт/.test(k));
    if ((task || own) && (targets(taskCell).length > 1 || plain(taskCell.replace(LINK, "")).replace(/[\s·,;—-]/g, ""))) extra.unshift(["задача", taskCell]);
    extra.forEach(([k, v]) => { const e = h(c, "div", muted(2), `${k}: `); rich(e, v, day.file.path).title = plain(v); });
    const up = h(c, "div", chip);
    h(up, "span", (mine ? dot(hue(proj)) : ring) + pin);
    if (task) {
      const path = [task.id ?? task.file.name, n ? `результат ${n}` : null, proj ? `${pid(proj)}${mine || n ? "" : " · фон"}` : null].filter(Boolean).join(" → ");
      link(h(up, "span", "min-width:0;", `↑ ${path}`), task.file.path, day.file.path);
    } else if (own) {
      link(h(up, "span", "min-width:0;", `↑ ${pid(proj)}${goal ? ` · цель ${goal.i + 1}` : mine ? " · ролевая цель" : " · фон"}`), own.file.path, day.file.path);
    } else h(up, "span", "min-width:0;color:var(--text-faint);", `↑ ${plain(taskCell) || "—"} · не задача`);
  });
}

// Week time (optional). week-time.md is regenerated from the Super Productivity backup
// by 80-kernel/scripts/week-time.py; without one for this week the block says so instead of
// showing a number that looks live.
const hm = s => { const m = String(s ?? "").match(/(\d+):(\d\d)/); return m ? +m[1] * 60 + +m[2] : null; };
const fmt = m => `${Math.floor(m / 60)}:${String(m % 60).padStart(2, "0")}`;
const week = isoWeek(today);
const tosH = +(section(sprintTxt, "ТОС спринта").match(/≥\s*(\d+)\s*ч в неделю/)?.[1] ?? NaN);
const tile = (g, title, big, sub, color) => {
  const c = card(g, color);
  h(c, "div", "font-size:12px;color:var(--text-muted);", title);
  h(c, "div", "font-size:26px;font-weight:600;line-height:1.1;font-variant-numeric:tabular-nums;", big);
  if (sub) h(c, "div", "font-size:12px;color:var(--text-muted);", sub);
  return c;
};
const meter = (c, value, limit, tone) => {
  const max = Math.max(limit * 1.5, value), bar = h(c, "div", "position:relative;height:5px;margin-top:2px;border-radius:3px;background:var(--background-modifier-border);");
  h(bar, "div", `position:absolute;left:0;top:0;bottom:0;width:${value / max * 100}%;border-radius:3px;background:${tone};`);
  h(bar, "div", `position:absolute;left:${limit / max * 100}%;top:-3px;bottom:-3px;width:2px;background:var(--text-normal);`).title = `порог ${fmt(limit)}`;
};
// Raw frontmatter: Dataview reads a bare "2026-W41" and the stamp as dates.
const wt = plans.find(p => p.type === "week-time") ?? null;
const live = wt && String(wt.file.frontmatter?.week) === week ? wt.file.frontmatter : null;

if (live) {
  const num = k => Number(live[k]) || 0;
  const outside = num("invested_outside_role"), all = num("tracked"), asOf = String(live.as_of ?? "");
  // The live week is always inside its own run, so a shortfall is what remains, not a miss.
  const limit = sprint && ymd(sprint.valid_from) <= today && Number.isFinite(tosH) ? tosH * 60 : null;
  const ok = limit != null && outside >= limit;
  label(false, "Время недели", { label: `неделя ${week}`, path: wt.file.path },
    /^\d{4}-\d\d-\d\d \d\d:\d\d/.test(asOf) ? `по данным на ${dm(asOf)} ${asOf.slice(11, 16)}` : null);
  const g = grid(), tone = ok ? "var(--color-green)" : "var(--text-faint)";
  const c = tile(g, "Инвестированное вне роли", fmt(outside),
    limit == null ? "порог ТОС в плане спринта не найден" : `ТОС спринта ≥${tosH} ч · ${ok ? "взят" : `до порога ${fmt(limit - outside)}`}`, tone);
  if (limit != null) meter(c, outside, limit, tone);
  tile(g, "Доля от учтённого", all ? `${Math.round(outside / all * 100)} %` : "—", all ? `${fmt(outside)} из ${fmt(all)}` : "за неделю ещё ничего не учтено", "var(--text-faint)");
  tile(g, "Учтено всего", fmt(all), `роль ${fmt(num("role"))} · личное ${fmt(num("personal"))}`, "var(--text-faint)");
  h(this.container, "div", "margin-top:6px;font-size:12px;color:var(--text-faint);",
    `Тег «Инвестированное» целиком — ${fmt(num("invested"))}, в задачах роли из них ${fmt(num("invested") - outside)}. Пересчёт из бэкапа Super Productivity; отметка времени стоит, пока числа не сменились.`);
} else {
  label(false, "Время недели", null, `неделя ${week}`);
  empty("Снимка времени этой недели нет. Блок опционален: 7-plans/current/week-time.md пишет 80-kernel/scripts/week-time.py из бэкапа Super Productivity — запуск по расписанию на ваш выбор.");
}
```

# Дневник

```meta-bind-button
label: Создать запись дня
icon: ""
hidden: false
class: ""
tooltip: ""
id: ""
style: default
actions:
  - type: templaterCreateNote
    templateFile: 80-kernel/templates/daily-tmpl.md
    folderPath: 20-library/journal
    fileName: daily
    openNote: true
```

# Важное

> [!abstract]- Стратегия
> [[strategy|Стратегия]] · [[strategize-agenda|Повестка стратегирования]] · [[10-governance/index|Реестр проектов]]

> [!todo]- Планы и лотки
> ```dataviewjs
> // Ссылки строятся из ФАКТИЧЕСКИХ файлов, а не из формулы по дате (ADR-0037): имя,
> // собранное из dateformat, после смены каденции ведёт на файлы, которых больше нет,
> // а имя юнита (YYYY-wNN-wMM) из даты не выводится вовсе — нужна чётность недели в юните.
> const list = (dir, suffix) => app.vault.getFiles()
>   .filter(f => f.path.startsWith(dir) && f.name.endsWith(suffix))
>   .sort((a, b) => a.name.localeCompare(b.name));
> const md = arr => arr.length ? arr.map(f => `[[${f.path}|${f.basename}]]`).join(" · ") : "—";
> const today = window.moment().format("YYYY-MM-DD");
> const day = app.vault.getAbstractFileByPath(`10-governance/7-plans/current/dayplan-${today}.md`);
> dv.paragraph("**Планы:** " + (day ? `[[${day.path}|План дня]]` : "план дня не создан — `/open`")
>   + " · " + md(list("10-governance/7-plans/current/", "-unitplan.md"))
>   + " · " + md(list("10-governance/7-plans/current/", "-sprintplan.md"))
>   + " · [Google Calendar](https://calendar.google.com/calendar/u/0/r/week)");
> dv.paragraph("**Лотки выноса** (каденции две — юнит и спринт)**:** "
>   + md(list("10-governance/7-plans/review/", "-forreview.md")));
> ```

# Фокус

```dataview
LIST FROM #фокус SORT file.mtime DESC
```

# Проекты

Проекты, их ранг и задачи — на странице [[self-model|«Модель меня»]].

```meta-bind-button
label: Завести проект
icon: ""
hidden: false
class: ""
tooltip: ""
id: ""
style: default
actions:
  - type: templaterCreateNote
    templateFile: 80-kernel/templates/project-tmpl.md
    folderPath: 10-governance/5-projects
    openNote: true
```

# Юнит
**Задачи в работе & Временной бюджет**
```dataviewjs
// Текущий юнит читается из ИМЕНИ файла UnitPlan в 7-plans/current/ — у юнита есть
// собственный артефакт (ADR-0037), и он же его называет. Истина в настройке вида
// (фильтр доски) требовала бы править доску каждые две недели. Тот же источник читает
// orz-check — второй список неизбежно разъехался бы.
let unit = null;
{
  const f = app.vault.getFiles()
    .find(x => x.path.startsWith("10-governance/7-plans/current/") && x.name.endsWith("-unitplan.md"));
  if (f) unit = f.name.replace(/-unitplan\.md$/, "");
}
const norm = v => (v === null || v === undefined) ? "" : String(v).trim();
const CLOSED = ["closed", "done", "later"];
const today = dv.date("today");

const all = dv.pages('"10-governance/6-tasks"').array()
  .filter(p => norm(p.type) === "task");
const open = all.filter(p => !CLOSED.includes(norm(p.status)))
                .filter(p => !p.awaiting || p.awaiting <= today);

// Оценка — номинал задачи. Дня здесь нет намеренно: раскладка по дням ведётся
// кейс-менеджментом (выбор на день в начале дня либо вечером накануне), а не вперёд на юнит.
const hrs = p => (p.budget_h === null || p.budget_h === undefined) ? null : Number(p.budget_h);
// Остаток = номинал минус снимок факта из прибора. `spent_h` — снимок, а не вторая истина:
// дата в `spent_checked` делает устаревание видимым (приём тот же, что у `priority_updated`).
const left = p => { const b = hrs(p); if (b === null) return null;
  return Math.max(0, Math.round((b - Number(p.spent_h || 0)) * 10) / 10); };
const row = p => [p.file.link, p.status, p.project,
  hrs(p) === null ? "—" : hrs(p) + " ч",
  left(p) === null ? "—" : left(p) + " ч"];
const COLS = ["Задача", "Статус", "Проект", "Оценка", "Осталось"];
const sum = arr => arr.reduce((a, p) => a + (hrs(p) || 0), 0);
const sumLeft = arr => Math.round(arr.reduce((a, p) => a + (left(p) || 0), 0) * 10) / 10;
const stale = arr => arr.filter(p => !p.spent_checked).length;

if (!unit) {
  dv.paragraph("⛔ В `plans/current/` нет файла `*-unitplan.md` — юнит не открыт; показаны все открытые задачи.");
  dv.table(COLS, open.map(row));
} else {
  const taken = open.filter(p => norm(p.unit) === norm(unit));
  // Ёмкость юнита в часах — ваша базовая величина: слоты будней + часы выходных на личные проекты
  // (повестка, «Ёмкость юнита»). Опора, а не расчёт: правится фактом на сверке. 0 — абзац не выводится.
  const BUDGET = 0;
const left0 = sumLeft(taken);
dv.paragraph(`Юнит **${unit}** — взято ${taken.length} из ${open.length} открытых. ` +
    `Номинал ${sum(taken)} ч, **осталось ${left0} ч**` +
    (stale(taken) ? ` · ⚠️ без снимка факта: ${stale(taken)}` : ""));
if (BUDGET) dv.paragraph(`Бюджет юнита **${BUDGET} ч**. ` +
    `Задачи забирают **${Math.round(left0 / BUDGET * 100)}%**; остальное — постоянные работы ` +
    `(чтение, письмо, сессии) и текучка. Величина базовая, правится фактом на сверке.`);
  if (taken.length) {
    dv.table(COLS, taken.map(row));
  } else {
    dv.paragraph("⛔ На юнит не взято ни одной работы — отбор не проведён (шаг 9).");
    dv.paragraph("Значения `unit` в карточках: " + [...new Set(open.map(p => norm(p.unit) || "—"))].join(" · "));
  }
}
```

> [!note]- Активные, но не взятые в юнит (петля открыта, внимания на эти две недели не требуют)
> ```dataviewjs
> const f = app.vault.getFiles().find(x => x.path.startsWith("10-governance/7-plans/current/") && x.name.endsWith("-unitplan.md"));
> const unit = f ? f.name.replace(/-unitplan\.md$/, "") : null;
> const norm = v => (v === null || v === undefined) ? "" : String(v).trim();
> const CLOSED = ["closed", "done", "later"];
> const today = dv.date("today");
> const rest = dv.pages('"10-governance/6-tasks"').array()
>   .filter(p => norm(p.type) === "task")
>   .filter(p => !CLOSED.includes(norm(p.status)))
>   .filter(p => !p.awaiting || p.awaiting <= today)
>   .filter(p => norm(p.unit) !== norm(unit));
> dv.table(["Задача", "Статус", "Проект", "Оценка"], rest.map(p => [p.file.link, p.status, p.project, p.budget_h ? p.budget_h + " ч" : "—"]));
> ```

> [!note]- Задачи, ждущие назначенной даты (петля открыта, действий не требуют)
> ```dataview
> TABLE awaiting AS "Ждёт до", status AS "Статус", link(project, project.aliases[0]) AS "Проект"
> FROM "10-governance/6-tasks"
> WHERE status != "closed" AND status != "done" AND status != "later"
>   AND awaiting > date(today)
> SORT awaiting ASC
> ```

# Курсы — прохожу

```dataview
LIST WHERE type = "course" AND status != "done" AND status != "later" AND !contains(file.path, "80-kernel")
SORT file.mtime DESC
```

> [!note]- Курсы — отложил
> ```dataview
> LIST WHERE type = "course" AND status = "later"
> SORT file.mtime DESC
> ```

# Книги — читаю

```dataview
LIST WHERE type = "book" AND status = "in-progress"
SORT file.mtime DESC
```

> [!note]- Книги — отложил
> ```dataview
> LIST WHERE type = "book" AND status = "later"
> SORT file.mtime DESC
> ```

# Черновики в работе

```meta-bind-button
label: Завести черновик
icon: ""
hidden: false
class: ""
tooltip: ""
id: ""
style: default
actions:
  - type: templaterCreateNote
    templateFile: 80-kernel/templates/draft-tmpl.md
    folderPath: 20-library/drafts
    openNote: true
```

```meta-bind-button
label: Начать текст
icon: ""
hidden: false
class: ""
tooltip: "Текст из черновика: шаблон спросит род, домен и черновик-источник"
id: ""
style: default
actions:
  - type: templaterCreateNote
    templateFile: 80-kernel/templates/text-tmpl.md
    folderPath: 20-library/posts
    openNote: true
```

```dataviewjs
await dv.view("20-library/pipeline/views/drafts-panel", { mode: "start" });

// Texts being written: a dated post until it is published, an evergreen until its first revision.
// Not every text is written in one sitting; while it is in work, it hangs here in sight.
const title = p => (p.aliases ?? [])[0] ?? p.file.name;
const h = (parent, tag, css, text) => {
  const e = parent.appendChild(document.createElement(tag));
  e.style.cssText = css;
  if (text != null) e.textContent = text;
  return e;
};
const link = (e, path) => {
  e.style.cursor = "pointer";
  e.addEventListener("click", ev => app.workspace.openLinkText(path, "", ev.metaKey || ev.ctrlKey));
  e.addEventListener("mouseover", ev => app.workspace.trigger("hover-link", {
    event: ev, source: "preview", hoverParent: this.container, targetEl: e, linktext: path,
  }));
  return e;
};
const faint = "font-size:13px;color:var(--text-faint);";
const line = "font-size:13px;color:var(--text-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;";
const plural = (n, [one, few, many]) =>
  n % 10 === 1 && n % 100 !== 11 ? one : n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20) ? few : many;

const today = new Date();
today.setHours(0, 0, 0, 0);
// Raw frontmatter keeps the YYYY-MM-DD string; a parsed Luxon date is the fallback.
const dateOf = v => {
  if (v?.toJSDate) { const d = v.toJSDate(); return new Date(d.getFullYear(), d.getMonth(), d.getDate()); }
  const m = String(v ?? "").match(/^(\d{4})-(\d{2})-(\d{2})/);
  return m ? new Date(+m[1], m[2] - 1, +m[3]) : null;
};
const filled = v => [v].flat().some(x => x != null && String(x).trim());
// A frontmatter link arrives as a Link, as a quoted "[[name|alias]]", or unquoted, which YAML reads as a nested list.
const names = v => [v ?? []].flat(Infinity)
  .map(x => x?.path ?? String(x).replace(/^\s*\[\[|\]\]\s*$/g, ""))
  .map(s => s.split(/[|#]/)[0].split("/").pop().replace(/\.md$/, "").trim())
  .filter(Boolean);
const since = p => {
  const c = dateOf(p.file.frontmatter?.created ?? p.created);
  if (c) return c;
  const t = new Date(+p.file.ctime);
  t.setHours(0, 0, 0, 0);
  return t;
};

const KINDS = [
  ["20-library/posts", "post", "published", "датированный"],
  ["20-library/evergreen", "evergreen", "revised", "вечнозелёный"],
];
const work = KINDS.flatMap(([dir, type, done, kind]) => dv.pages(`"${dir}"`)
  .where(p => p.type === type && !filled(p.file.frontmatter?.[done]))
  .array().map(p => ({ p, kind, from: since(p) })))
  .sort((a, b) => a.from - b.from);

h(this.container, "div", "margin:16px 0 6px;font-size:13px;font-weight:600;color:var(--text-muted);", `Публикации в работе · ${work.length}`);
if (!work.length) h(this.container, "div", faint, "в работе ничего нет");
const grid = h(this.container, "div", "display:grid;grid-template-columns:repeat(auto-fill,minmax(max(166px,calc((100% - 20px) / 3)),1fr));gap:10px;");

work.forEach(({ p, kind, from }) => {
  const card = h(grid, "div", "display:flex;flex-direction:column;gap:5px;min-width:0;padding:8px 10px;border-radius:6px;line-height:1.35;color:var(--text-normal);background:var(--background-secondary);border:1px solid var(--background-modifier-border);border-left:3px solid var(--text-accent);");
  link(h(card, "div", "font-size:13.5px;font-weight:600;min-width:0;", title(p)), p.file.path).title = p.file.name;

  const n = Math.round((today - from) / 864e5);
  const big = h(card, "div", "display:flex;align-items:baseline;gap:8px;");
  h(big, "span", "font-size:28px;font-weight:600;line-height:1.1;", String(n));
  h(big, "span", "font-size:13px;color:var(--text-muted);", `${plural(n, ["день", "дня", "дней"])} в работе`);

  h(card, "div", line, [kind, p.domain].filter(Boolean).join(" · "));

  // A dangling source stays visible, so a renamed draft shows up as a gap instead of vanishing.
  const src = names(p.drafts).map(n => ({ n, d: dv.page(n) }));
  const row = h(card, "div", line, src.length ? "из черновиков: " : "");
  if (!src.length) h(row, "span", "color:var(--text-faint);", "не из черновика");
  src.forEach(({ n, d }, i) => {
    if (i) row.append(", ");
    if (d) link(h(row, "span", "color:var(--text-normal);", `${String(d.id ?? "").toUpperCase()} ${title(d)}`.trim()), d.file.path).title = d.file.name;
    else h(row, "span", "color:var(--text-faint);", `${n} — не найден`);
  });
});
```

---

> [!info]- Недавно изменённые
> ```dataview
> TABLE file.mtime AS "Изменён"
> FROM "00-inbox" OR "20-library" OR "30-knowledge" OR "10-governance"
> SORT file.mtime DESC
> LIMIT 15
> ```

> [!info]- Заметки-обрубки (пустые заглушки <300 байт)
> ```dataview
> TABLE file.size AS "Размер"
> FROM "20-library" OR "30-knowledge"
> WHERE file.size < 300
> SORT file.size ASC
> LIMIT 20
> ```
