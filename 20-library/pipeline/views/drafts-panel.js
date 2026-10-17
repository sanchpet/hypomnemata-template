// Drafts panel of the creative pipeline, and the one home of the draft priority rule and of draft mass.
// Called as dv.view("20-library/pipeline/views/drafts-panel", { mode }): "all" on creative-pipeline.md, "start" on start.md.
// The header of 80-kernel/templates/draft-tmpl.md repeats the rule for a single draft; change it together with this file.
// dv.view runs this file through new Function("dv", "input", …), so there is no `this`: the container is dv.container.
const mode = input?.mode ?? "all";
const root = dv.container;
const CANDIDATES = 3;

const num = p => parseInt(String(p.id ?? "").match(/\d+/)?.[0]) || 999;
const title = p => (p.aliases ?? [])[0] ?? p.file.name;
const ROOT = "20-library/drafts", ARCHIVE = `${ROOT}/archive`;
const under = (p, dir) => (p.file.folder + "/").startsWith(dir + "/");

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
    event: ev, source: "preview", hoverParent: root, targetEl: e, linktext: path,
  }));
  return e;
};
const faint = "font-size:13px;color:var(--text-faint);";
const line = "font-size:13px;color:var(--text-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;";
const plural = (n, [one, few, many]) =>
  n % 10 === 1 && n % 100 !== 11 ? one : n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20) ? few : many;

// A frontmatter link arrives as a Link, as a quoted "[[name|alias]]", or unquoted, which YAML reads as a nested list.
const names = v => [v ?? []].flat(Infinity)
  .map(x => x?.path ?? String(x).replace(/^\s*\[\[|\]\]\s*$/g, ""))
  .map(s => s.split(/[|#]/)[0].split("/").pop().replace(/\.md$/, "").trim())
  .filter(Boolean);
const rank = v => { const n = Number(v); return Number.isInteger(n) && n > 0 ? n : null; };
const CLOSED = ["done", "closed", "archived", "merged"];
const isAsp = p => under(p, "10-governance/2-aspirations");
const activeProject = p => !p.file.folder.includes("archive") && !CLOSED.includes(String(p.status ?? "").toLowerCase());

// Mass counts only the entries that fed the draft; tasks, cards, sessions, reasons and this page link it too, but feed nothing.
const KINDS = [["learn-note", "заметки"], ["finding", "находки"], ["conversation", "беседы"], ["journal", "дневник"]];
const massOf = d => {
  const by = Object.fromEntries(KINDS.map(([k]) => [k, 0]));
  for (const path of new Set((d.file.inlinks ?? []).map(l => l.path))) {
    const t = dv.page(path)?.type;
    if (t in by) by[t]++;
  }
  return {
    total: Object.values(by).reduce((a, b) => a + b, 0),
    parts: KINDS.filter(([k]) => by[k]).map(([k, label]) => `${label} ${by[k]}`),
  };
};

// README of the drafts folder describes the folder and is not a draft.
const drafts = dv.pages(`"${ROOT}"`).where(p => !under(p, ARCHIVE) && p.file.name !== "README").array().map(d => {
  const asp = names(d.aspiration).map(n => ({ n, p: dv.page(n) }));
  const projects = names(d.projects).map(n => ({ n, p: dv.page(n) }));
  const live = projects.filter(x => x.p && activeProject(x.p));
  // The highest-ranked live project lifts the draft; a live project without a rank still lifts it, below the ranked ones.
  const lift = live.map(x => ({ p: x.p, r: rank(x.p.priority) ?? Infinity })).sort((a, b) => a.r - b.r)[0] ?? null;
  const own = rank(d.priority);
  return {
    d, asp, projects, own, lift,
    mass: massOf(d),
    hasAsp: asp.some(x => x.p && isAsp(x.p)),
    group: own ? 0 : lift ? 1 : 2,
  };
});

const byMass = (a, b) => b.mass.total - a.mass.total || num(a.d) - num(b.d);
const GROUPS = [
  ["Приоритетные", "var(--color-yellow)", (a, b) => a.own - b.own || byMass(a, b)],
  ["По проектам", "var(--color-cyan)", (a, b) => a.lift.r - b.lift.r || byMass(a, b)],
  ["Прочие", "var(--background-modifier-border)", byMass],
];
const pid = p => p.id ?? p.file.name;
const source = x => x.own ? `№${x.own}` : x.lift ? `↑ ${pid(x.lift.p)}${x.lift.r < Infinity ? ` №${x.lift.r}` : ""}` : "";
const ofGroup = g => drafts.filter(x => x.group === g).sort(GROUPS[g][2]);
const gridOf = css => h(root, "div", `display:grid;grid-template-columns:repeat(auto-fill,minmax(max(166px,calc((100% - 20px) / 3)),1fr));gap:10px;${css}`);

const card = (grid, x, color) => {
  const { d, mass } = x;
  const card = h(grid, "div", `display:flex;flex-direction:column;gap:5px;min-width:0;padding:8px 10px;border-radius:6px;line-height:1.35;color:var(--text-normal);background:var(--background-secondary);border:1px solid var(--background-modifier-border);border-left:3px solid ${color};`);

  const head = h(card, "div", "display:flex;align-items:baseline;gap:6px;font-size:13.5px;min-width:0;");
  h(head, "span", "font-size:12px;color:var(--text-muted);white-space:nowrap;", String(d.id ?? "").toUpperCase());
  link(h(head, "span", "flex:1;min-width:0;font-weight:600;", title(d)), d.file.path).title = d.file.name;
  if (source(x)) h(head, "span", "font-size:12px;color:var(--text-muted);white-space:nowrap;", source(x));

  const big = h(card, "div", "display:flex;align-items:baseline;gap:8px;");
  h(big, "span", `font-size:28px;font-weight:600;line-height:1.1;${mass.total ? "" : "color:var(--text-faint);"}`, String(mass.total));
  h(big, "span", "font-size:13px;color:var(--text-muted);", mass.total ? `${plural(mass.total, ["вход", "входа", "входов"])}: ${mass.parts.join(" · ")}` : "входов нет");

  // Every draft must serve an aspiration; a missing or unresolved one is a violation, not a gap to fill later.
  const asp = h(card, "div", line, "устремление: ");
  if (!x.asp.length) h(asp, "span", "color:var(--text-error);font-weight:600;", "нет устремления");
  x.asp.forEach(({ n, p }, i) => {
    if (i) asp.append(", ");
    if (p && isAsp(p)) link(h(asp, "span", "color:var(--text-normal);", `${p.id ?? ""} ${title(p)}`.trim()), p.file.path).title = p.file.name;
    else h(asp, "span", "color:var(--text-error);", `${n} — ${p ? "не устремление" : "не найдено"}`);
  });

  if (x.projects.length) {
    const row = h(card, "div", line, "проекты: ");
    x.projects.forEach(({ n, p }, i) => {
      if (i) row.append(" · ");
      if (!p) return h(row, "span", "color:var(--text-faint);", `${n} — не найден`);
      const r = rank(p.priority), on = activeProject(p);
      const e = link(h(row, "span", on ? "color:var(--text-normal);" : "color:var(--text-faint);", `${pid(p)}${r && on ? ` №${r}` : ""}${on ? "" : " (закрыт)"}`), p.file.path);
      e.title = title(p);
    });
  }
};

if (mode === "start") {
  // Start shows only what the unit committed to; with nothing chosen, the project-lifted drafts hint where to look.
  const [label, color] = GROUPS[0];
  const top = ofGroup(0);
  h(root, "div", "margin:4px 0 6px;font-size:13px;font-weight:600;color:var(--text-muted);", `${label} черновики · ${top.length}`);
  if (top.length) {
    const grid = gridOf("");
    top.forEach(x => card(grid, x, color));
  } else {
    h(root, "div", faint, "приоритетные не выбраны — выбираются на стратегировании юнита");
    const next = ofGroup(1).slice(0, CANDIDATES);
    if (next.length) {
      h(root, "div", `${faint}margin:10px 0 6px;`, `кандидаты по проектам · ${next.length} из ${ofGroup(1).length}`);
      const grid = gridOf("opacity:0.55;");
      next.forEach(x => card(grid, x, GROUPS[1][1]));
    }
  }
} else {
  const archived = dv.pages(`"${ARCHIVE}"`).length;
  const noAsp = drafts.filter(x => !x.hasAsp).length;
  h(root, "div", "margin:4px 0 2px;font-size:13px;color:var(--text-muted);",
    `активных ${drafts.length} · приоритетных ${drafts.filter(x => x.group === 0).length} · без устремления ${noAsp} · в архиве ${archived}`);
  if (!drafts.length) h(root, "div", faint, "Черновиков пока нет");

  GROUPS.forEach(([label, color], g) => {
    const group = ofGroup(g);
    if (!group.length) return;
    h(root, "div", "margin:16px 0 6px;font-size:13px;font-weight:600;color:var(--text-muted);", `${label} · ${group.length}`);
    const grid = gridOf("");
    group.forEach(x => card(grid, x, color));
  });
}
