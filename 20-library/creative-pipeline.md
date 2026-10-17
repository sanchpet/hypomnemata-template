---
type: system
aliases: ["Модель творческого конвейера", "Creative pipeline"]
---

# Модель творческого конвейера

> Всё о творческом конвейере на одном экране. Страница ничего не хранит сама — только показывает: истина живёт в карточках поводов, а дальше — входов, стадий, черновиков и публикаций. Собирается панелями по порядку: поводы письма → входы → черновики → публикации. Модель — INV-12; карточки поводов и входов лежат в `20-library/pipeline/`.

## Поводы письма

```dataviewjs
const num = p => parseInt(String(p.id ?? "").match(/\d+/)?.[0]) || 999;
const title = p => (p.aliases ?? [])[0] ?? p.file.name;
const base = l => String(l?.path ?? l ?? "").split("/").pop().replace(/\.md$/, "");
const live = p => !p.file.folder.includes("archive");
const many = v => [v ?? []].flat().filter(Boolean);

// Green marks the sprint on the self-model, so orientations take other slots.
const ORIENT = [
  ["inward", "Внутрь — для себя", "var(--color-blue)"],
  ["outward", "Наружу — для читателя", "var(--color-orange)"],
  ["circle", "К кругу", "var(--color-purple)"],
];
const reasons = dv.pages('"20-library/pipeline/reasons"').where(p => p.type === "writing-reason" && live(p)).sort(num).array();

const h = (parent, tag, css, text) => {
  const e = parent.appendChild(document.createElement(tag));
  e.style.cssText = css;
  if (text != null) e.textContent = text;
  return e;
};
const link = (e, p) => {
  e.style.cursor = "pointer";
  e.addEventListener("click", ev => app.workspace.openLinkText(p.file.path, "", ev.metaKey || ev.ctrlKey));
  e.addEventListener("mouseover", ev => app.workspace.trigger("hover-link", {
    event: ev, source: "preview", hoverParent: this.container, targetEl: e, linktext: p.file.path,
  }));
  return e;
};
const dot = color => `display:inline-block;flex:none;width:7px;height:7px;border-radius:50%;background:${color};`;
const ring = `${dot("transparent")}box-shadow:inset 0 0 0 1.5px var(--text-faint);`;
const line = "display:flex;align-items:center;gap:6px;font-size:13px;min-width:0;";
const clip = "flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;";
const muted = "font-size:13px;color:var(--text-muted);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;";

// A draft is anything under 20-library/drafts (archive included); everything else an example points to has been published.
const isDraft = p => (p.file.folder + "/").startsWith("20-library/drafts/");

ORIENT.forEach(([code, label, color], rank) => {
  const group = reasons.filter(r => r.orientation === code);
  if (!group.length) return;
  h(this.container, "div", `margin:${rank ? 16 : 4}px 0 6px;font-size:13px;font-weight:600;color:var(--text-muted);`, `${label} · ${group.length}`);
  const grid = h(this.container, "div", "display:grid;grid-template-columns:repeat(auto-fill,minmax(max(166px,calc((100% - 20px) / 3)),1fr));gap:10px;");

  group.forEach(r => {
    const card = h(grid, "div", `display:flex;flex-direction:column;gap:5px;min-width:0;padding:8px 10px;border-radius:6px;line-height:1.35;color:var(--text-normal);background:var(--background-secondary);border:1px solid var(--background-modifier-border);border-left:3px solid ${color};`);

    const head = h(card, "div", "font-size:13.5px;");
    h(head, "span", "font-size:12px;color:var(--text-muted);white-space:nowrap;", r.id);
    head.append(" ");
    link(h(head, "span", "font-weight:600;", title(r)), r);

    if (r.statement) h(card, "div", `${muted}color:var(--text-normal);`, r.statement).title = r.statement;
    if (r.sign) h(card, "div", `${muted}font-style:italic;`, r.sign).title = r.sign;

    // Unresolved links stay visible, so a renamed post shows up as a gap instead of vanishing from the count.
    const ex = many(r.examples).map(l => ({ name: base(l), p: dv.page(base(l)) }));
    const posts = ex.filter(x => x.p && !isDraft(x.p)), drafts = ex.filter(x => x.p && isDraft(x.p)), lost = ex.filter(x => !x.p);
    const box = h(card, "details", "font-size:13px;");
    const parts = [`${posts.length} опубл.`, `${drafts.length} черн.`].concat(lost.length ? [`${lost.length} не найдено`] : []);
    h(box, "summary", "cursor:pointer;color:var(--text-muted);", ex.length ? `Примеры: ${parts.join(" · ")}` : "Примеров нет");
    [...posts, ...drafts].forEach(({ p }) => {
      const row = h(box, "div", `${line}margin-top:3px;`);
      h(row, "span", isDraft(p) ? ring : dot(color));
      link(h(row, "span", clip, title(p)), p).title = `${title(p)} — ${p.file.name}`;
    });
    lost.forEach(({ name }) => h(box, "div", `${line}margin-top:3px;color:var(--text-faint);`, `${name} — файла нет`));
  });
});

const stray = reasons.filter(r => !ORIENT.some(([code]) => code === r.orientation));
if (stray.length) {
  const note = h(this.container, "div", "margin-top:10px;font-size:12.5px;color:var(--text-faint);", `Без ориентации: ${stray.length} — `);
  stray.forEach((r, i) => { if (i) note.append(", "); link(h(note, "span", "", title(r)), r); });
}
```

## Входы

```dataviewjs
const num = p => parseInt(String(p.id ?? "").match(/\d+/)?.[0]) || 999;
const title = p => (p.aliases ?? [])[0] ?? p.file.name;
const entries = dv.pages('"20-library/pipeline/entries"').where(p => p.type === "writing-entry" && p.status === "active").sort(num).array();

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

const today = new Date();
today.setHours(0, 0, 0, 0);
// First valid DD.MM[.YYYY] in a line; a yearless date that would lie ahead belongs to last year.
const dateIn = s => {
  for (const m of s.matchAll(/(?<![\d.])(\d{2})\.(\d{2})(?:\.(\d{4}))?(?!\d)/g)) {
    const d = +m[1], mo = +m[2], y = m[3] ? +m[3] : today.getFullYear();
    const t = new Date(y, mo - 1, d);
    if (t.getMonth() !== mo - 1 || t.getDate() !== d) continue;
    return !m[3] && t > today ? new Date(y - 1, mo - 1, d) : t;
  }
  return null;
};

// The card names its rule in count_rule. A rule reads the carrier (and the card, for any other path it names) and returns { count, oldest?, note? },
// or null when the carrier is missing; words caption the count, empty replaces them at zero.
// The «Публикации» panel repeats linked; change both together.
const linked = v => typeof v === "string" ? /\[\[[^\]]+\]\]/.test(v) : Boolean(v?.path);
const createdOf = p => {
  const m = String(p.file.frontmatter?.created ?? "").match(/^(\d{4})-(\d{2})-(\d{2})/);
  return m ? new Date(+m[1], m[2] - 1, +m[3]) : null;
};
// A journal entry's day: created, else the D-NNN-DD-month-YYYY file name.
const MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"];
const dayOf = p => {
  const c = createdOf(p);
  if (c) return c;
  const m = p.file.name.match(/(\d{2})-([a-z]+)-(\d{4})$/);
  return m && MONTHS.includes(m[2]) ? new Date(+m[3], MONTHS.indexOf(m[2]), +m[1]) : null;
};
// Every note in the tray counts, formed or not; a processed note has moved to home_after and links a draft.
// The card names the expected note type in item_type, so a tray rule differs from another only in its words.
const trayCount = async (path, e) => {
  if (!app.vault.getAbstractFileByPath(path)) return null;
  const type = e.item_type ?? "finding";
  // README лотка описывает лоток и в счёт не входит.
  const tray = dv.pages(`"${path}"`).array().filter(p => p.file.name !== "README");
  const days = tray.map(p => {
    const c = createdOf(p);
    if (c) return c;
    const t = new Date(+p.file.ctime);
    t.setHours(0, 0, 0, 0);
    return t;
  }).filter(d => !isNaN(d));
  const raw = tray.filter(p => p.type !== type).length;
  const home = e.home_after;
  const moved = home && app.vault.getAbstractFileByPath(home)
    ? dv.pages(`"${home}"`).where(p => p.type === type).array()
    : [];
  const done = moved.filter(p => [p.file.frontmatter?.drafts].flat().some(linked)).length;
  // Выход обязателен: перенесённая без черновика заметка иначе выпала бы из виду.
  const orphan = moved.length - done;
  return {
    count: tray.length,
    oldest: days.length ? new Date(Math.min(...days)) : null,
    note: [`разобрано: ${done}`]
      .concat(orphan ? [`перенесено без черновика: ${orphan}`] : [])
      .concat(raw ? [`без формы: ${raw}`] : []).join(" · "),
  };
};
const RULES = {
  "top-level-lines": {
    words: ["запись не разобрана", "записи не разобраны", "записей не разобрано"],
    empty: "лоток пуст",
    count: async path => {
      const text = await dv.io.load(path);
      if (text == null) return null;
      let lines = text.split(/\r?\n/);
      const end = lines[0]?.trim() === "---" ? lines.findIndex((l, i) => i > 0 && l.trim() === "---") : -1;
      if (end > 0) lines = lines.slice(end + 1);
      const items = lines.filter(l => /^[^\s>]/.test(l));
      const dates = items.map(dateIn).filter(Boolean);
      return { count: items.length, oldest: dates.length ? new Date(Math.min(...dates)) : null };
    },
  },
  // Raw frontmatter keeps an empty key (drafts: [] or drafts:), which the parsed field cannot tell from a missing one.
  "drafts-link": {
    words: ["новая не разобрана", "новые не разобраны", "новых не разобрано"],
    empty: "новых нет",
    count: async path => {
      if (!app.vault.getAbstractFileByPath(path)) return null;
      let fresh = 0, done = 0, debt = 0;
      for (const p of dv.pages(`"${path}"`).where(p => p.type === "learn-note")) {
        const fm = p.file.frontmatter ?? {};
        if (!("drafts" in fm)) debt++;
        else if ([fm.drafts].flat().some(linked)) done++;
        else fresh++;
      }
      return { count: fresh, note: `долг: ${debt} · разобрано: ${done}` };
    },
  },
  // Same raw-frontmatter reading: a bare reviewed: is not a review. Today's entry is still being written.
  "reviewed-key": {
    words: ["запись не перечитана", "записи не перечитаны", "записей не перечитано"],
    empty: "всё перечитано",
    count: async path => {
      if (!app.vault.getAbstractFileByPath(path)) return null;
      let count = 0;
      const days = [];
      for (const p of dv.pages(`"${path}"`).where(p => p.type === "journal")) {
        const fm = p.file.frontmatter ?? {};
        if ("reviewed" in fm && [fm.reviewed].flat().some(v => v != null && String(v).trim())) continue;
        const day = dayOf(p);
        if (day && +day === +today) continue;
        count++;
        if (day) days.push(day);
      }
      return { count, oldest: days.length ? new Date(Math.min(...days)) : null };
    },
  },
  "findings-tray": {
    words: ["находка не разобрана", "находки не разобраны", "находок не разобрано"],
    empty: "лоток пуст",
    count: trayCount,
  },
  "conversations-tray": {
    words: ["выжимка не разобрана", "выжимки не разобраны", "выжимок не разобрано"],
    empty: "лоток пуст",
    count: trayCount,
  },
};
const REVIEW_AT = {
  source: "разбор — при работе с источником",
  weekly: "разбор — на недельном стратегировании",
  mass: "разбор — по накоплению материала",
};

const plural = (n, [one, few, many]) =>
  n % 10 === 1 && n % 100 !== 11 ? one : n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20) ? few : many;
const ago = d => {
  const n = Math.round((today - d) / 864e5);
  return n ? `${n} ${plural(n, ["день", "дня", "дней"])} назад` : "сегодня";
};
const ddmm = d => [d.getDate(), d.getMonth() + 1].map(x => String(x).padStart(2, "0")).join(".");

if (!entries.length) h(this.container, "div", faint, "Входов пока нет");
const grid = h(this.container, "div", "display:grid;grid-template-columns:repeat(auto-fill,minmax(max(166px,calc((100% - 20px) / 3)),1fr));gap:10px;margin-top:4px;");

// Read the carrier on every render: the count must follow the tray live, not a cached figure.
for (const e of entries) {
  let res = null, why = null;
  const rule = RULES[e.count_rule];
  if (!e.carrier) why = "носитель не указан";
  else if (!rule) why = `нет правила подсчёта «${e.count_rule ?? "—"}»`;
  else {
    try {
      res = await rule.count(e.carrier, e);
      if (!res) why = `носителя нет — ${e.carrier}`;
    } catch (err) {
      why = `носитель не прочитан — ${err.message ?? err}`;
    }
  }

  const accent = res?.count ? "var(--text-accent)" : "var(--background-modifier-border)";
  const card = h(grid, "div", `display:flex;flex-direction:column;gap:5px;min-width:0;padding:8px 10px;border-radius:6px;line-height:1.35;color:var(--text-normal);background:var(--background-secondary);border:1px solid var(--background-modifier-border);border-left:3px solid ${accent};`);

  const head = h(card, "div", "font-size:13.5px;");
  h(head, "span", "font-size:12px;color:var(--text-muted);white-space:nowrap;", e.id);
  head.append(" ");
  link(h(head, "span", "font-weight:600;", title(e)), e.file.path);

  if (e.carrier) {
    const where = h(card, "div", "font-size:13px;color:var(--text-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;", "лежит: ");
    // A folder carrier gets no link: openLinkText on a folder path would create a note of that name.
    const isFile = /\.md$/.test(e.carrier);
    const name = h(where, "span", "color:var(--text-normal);", e.carrier.split("/").pop().replace(/\.md$/, "") + (isFile ? "" : "/"));
    (isFile ? link(name, e.carrier) : name).title = e.carrier;
  }

  if (!res) { h(card, "div", faint, `не считается: ${why}`); continue; }
  const big = h(card, "div", "display:flex;align-items:baseline;gap:8px;");
  h(big, "span", `font-size:28px;font-weight:600;line-height:1.1;${res.count ? "" : "color:var(--text-faint);"}`, String(res.count));
  h(big, "span", "font-size:13px;color:var(--text-muted);", res.count ? plural(res.count, rule.words) : rule.empty);
  if (res.oldest) h(card, "div", "font-size:13px;color:var(--text-muted);", `старейшая: ${ddmm(res.oldest)} · ${ago(res.oldest)}`);
  if (res.note) h(card, "div", "font-size:13px;color:var(--text-muted);", res.note);
  if (REVIEW_AT[e.review_at]) h(card, "div", faint, REVIEW_AT[e.review_at]);
}
```

## Черновики

```dataviewjs
// The priority rule and draft mass live in the module; start.md draws the same panel in its own mode.
await dv.view("20-library/pipeline/views/drafts-panel", { mode: "all" });
```

## Публикации

```dataviewjs
const title = p => (p.aliases ?? [])[0] ?? p.file.name;
const POSTS = "20-library/posts", EVERGREEN = "20-library/evergreen";
// Series threshold of the writing practice: a publication every week, GOAL weeks in a row, counted from START (a Monday).
// Both are yours: set them from the practice card's skill threshold.
const GOAL = 10, START = new Date(2027, 0, 4), STRIP = 12, RECENT = 5;

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
const muted = "font-size:13px;color:var(--text-muted);";
const card = `display:flex;flex-direction:column;gap:5px;min-width:0;padding:8px 10px;border-radius:6px;line-height:1.35;color:var(--text-normal);background:var(--background-secondary);border:1px solid var(--background-modifier-border);`;
const plural = (n, [one, few, many]) =>
  n % 10 === 1 && n % 100 !== 11 ? one : n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20) ? few : many;
const ddmm = d => [d.getDate(), d.getMonth() + 1].map(x => String(x).padStart(2, "0")).join(".") + `.${d.getFullYear()}`;

// Raw frontmatter keeps the YYYY-MM-DD string; a parsed Luxon date is the fallback.
const dateOf = v => {
  if (v?.toJSDate) { const d = v.toJSDate(); return new Date(d.getFullYear(), d.getMonth(), d.getDate()); }
  const m = String(v ?? "").match(/^(\d{4})-(\d{2})-(\d{2})/);
  return m ? new Date(+m[1], m[2] - 1, +m[3]) : null;
};
const monday = d => new Date(d.getFullYear(), d.getMonth(), d.getDate() - (d.getDay() + 6) % 7);
const shift = (d, weeks) => new Date(d.getFullYear(), d.getMonth(), d.getDate() + 7 * weeks);
const isoWeek = d => {
  const t = new Date(d.getFullYear(), d.getMonth(), d.getDate() + 3 - (d.getDay() + 6) % 7);
  // Rounding to whole days absorbs the DST hour between January and the Thursday.
  return { year: t.getFullYear(), week: 1 + Math.floor(Math.round((t - new Date(t.getFullYear(), 0, 1)) / 864e5) / 7) };
};
const wlabel = d => `W${isoWeek(d).week}`;
const firstLink = v => [v ?? []].flat().map(String).find(s => /^https?:\/\//.test(s)) ?? null;

const today = new Date();
today.setHours(0, 0, 0, 0);
const thisWeek = monday(today);

// The link rule of the «Входы» panel; blocks do not share scope, so it is repeated verbatim — change both together.
const linked = v => typeof v === "string" ? /\[\[[^\]]+\]\]/.test(v) : Boolean(v?.path);
const filled = v => [v].flat().some(x => x != null && String(x).trim());
// Every dated text with published is a publication, but the writing-practice series takes only one born from a draft
// or an announcement of an evergreen revision: it trains the path draft → text.
const dated = dv.pages(`"${POSTS}"`).where(p => p.type === "post").array();
const posts = dated.map(p => {
  const fm = p.file.frontmatter ?? {};
  return { p, day: dateOf(fm.published ?? p.published), series: [fm.drafts].flat().some(linked) || filled(fm.announces) };
});
const undated = posts.filter(x => !x.day).length;
const published = posts.filter(x => x.day && x.day <= today).sort((a, b) => b.day - a.day);
const byWeek = new Map();
published.forEach(x => {
  const k = +monday(x.day), w = byWeek.get(k) ?? { series: 0, other: 0 };
  w[x.series ? "series" : "other"]++;
  byWeek.set(k, w);
});
const count = d => byWeek.get(+d)?.series ?? 0;
const other = d => byWeek.get(+d)?.other ?? 0;

// The week in progress does not break the series until it ends empty.
const now = count(thisWeek);
let cursor = now ? thisWeek : shift(thisWeek, -1), streak = 0;
while (cursor >= START && count(cursor)) { streak++; cursor = shift(cursor, -1); }

const grid = h(this.container, "div", "display:grid;grid-template-columns:repeat(auto-fill,minmax(max(166px,calc((100% - 20px) / 3)),1fr));gap:10px;margin-top:4px;");
const week = h(grid, "div", `${card}border-left:3px solid ${now ? "var(--text-accent)" : "var(--background-modifier-border)"};`);
h(week, "div", "font-size:13.5px;font-weight:600;", `Эта неделя · ${wlabel(thisWeek)}`);
const wbig = h(week, "div", "display:flex;align-items:baseline;gap:8px;");
h(wbig, "span", `font-size:28px;font-weight:600;line-height:1.1;${now ? "" : "color:var(--text-faint);"}`, String(now));
h(wbig, "span", muted, now ? plural(now, ["публикация", "публикации", "публикаций"]) : "в серию пока нет");
h(week, "div", faint, "в серию — тексты из черновика и анонсы редакций");

const run = h(grid, "div", `${card}border-left:3px solid ${streak >= GOAL ? "var(--color-green)" : streak ? "var(--text-accent)" : "var(--background-modifier-border)"};`);
h(run, "div", "font-size:13.5px;font-weight:600;", "Серия недель подряд");
const rbig = h(run, "div", "display:flex;align-items:baseline;gap:8px;");
h(rbig, "span", `font-size:28px;font-weight:600;line-height:1.1;${streak ? "" : "color:var(--text-faint);"}`, String(streak));
h(rbig, "span", muted, `из ${GOAL} — порог практики письма`);
if (today < START) h(run, "div", faint, `отсчёт с ${wlabel(START)} ${isoWeek(START).year} · ${ddmm(START)}`);
else if (!now && streak) h(run, "div", "font-size:13px;color:var(--text-warning);", "на этой неделе публикации из черновика ещё нет — серия держится до воскресенья");

// One dot per week, oldest on the left; weeks before the series start are history and stay faint.
// Filled — the week counts; translucent — only publications outside the series; ring — nothing.
const strip = h(this.container, "div", "display:flex;gap:4px;margin-top:12px;flex-wrap:wrap;");
for (let i = STRIP - 1; i >= 0; i--) {
  const w = shift(thisWeek, -i), n = count(w), m = other(w), pre = w < START;
  const col = h(strip, "div", "display:flex;flex-direction:column;align-items:center;gap:2px;min-width:28px;");
  const fill = pre ? "var(--text-faint)" : "var(--text-accent)";
  const ring = `box-shadow:inset 0 0 0 1.5px ${pre ? "var(--background-modifier-border)" : "var(--text-faint)"};`;
  const dot = h(col, "span", `display:inline-block;width:10px;height:10px;border-radius:50%;${n ? `background:${fill};` : m ? `background:${fill};opacity:0.3;` : ring}${+w === +thisWeek ? "outline:1px solid var(--text-muted);outline-offset:2px;" : ""}`);
  if (!n && m) dot.title = "публикации есть, но не из черновика";
  h(col, "span", "font-size:11px;color:var(--text-faint);", wlabel(w)).title = `${wlabel(w)} ${isoWeek(w).year}: в серию ${n}${m ? `, прочих ${m}` : ""} · с ${ddmm(w)}`;
}

h(this.container, "div", "margin:14px 0 4px;font-size:13px;font-weight:600;color:var(--text-muted);", `Последние публикации · всего ${published.length}`);
if (!published.length) h(this.container, "div", faint, "Публикаций пока нет");
published.slice(0, RECENT).forEach(({ p, day, series }) => {
  const row = h(this.container, "div", "display:flex;align-items:baseline;gap:6px;font-size:13px;min-width:0;margin-top:3px;");
  h(row, "span", "font-size:12px;color:var(--text-muted);white-space:nowrap;", ddmm(day));
  link(h(row, "span", "flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;", title(p)), p.file.path).title = p.file.name;
  if (!series) h(row, "span", "font-size:12px;color:var(--text-faint);opacity:0.7;white-space:nowrap;", "не из черновика");
  const ch = [p.channels ?? []].flat().filter(Boolean).join(", ") + (p.announces ? " · анонс" : "");
  if (ch) h(row, "span", "font-size:12px;color:var(--text-faint);white-space:nowrap;", ch);
  const url = firstLink(p.file.frontmatter?.link ?? p.link);
  if (url) {
    const a = h(row, "a", "font-size:12px;white-space:nowrap;", "↗");
    a.href = url;
    a.title = url;
  }
});
if (undated) h(this.container, "div", "font-size:13px;color:var(--text-error);margin-top:6px;", `без даты публикации: ${undated}`);

// Evergreen texts live by revisions; their history is git, the page shows only the latest.
const green = dv.pages(`"${EVERGREEN}"`).where(p => p.type === "evergreen").array()
  .map(p => ({ p, day: dateOf(p.file.frontmatter?.revised ?? p.revised) }));
const latest = green.filter(x => x.day).sort((a, b) => b.day - a.day)[0];
const ev = h(this.container, "div", `${muted}margin-top:12px;`, `Вечнозелёных ${green.length}`);
if (latest) {
  ev.append(" · последняя редакция: ");
  link(h(ev, "span", "color:var(--text-normal);", title(latest.p)), latest.p.file.path).title = latest.p.file.name;
  ev.append(` — r${latest.p.revision ?? "?"}, ${ddmm(latest.day)}`);
}
```
