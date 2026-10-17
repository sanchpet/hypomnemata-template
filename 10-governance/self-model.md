---
type: system
aliases: ["Модель меня", "Self model"]
---

# Модель меня

> Всё важное обо мне на одном экране, собранное из реестров цепочки. Страница ничего не хранит сама — только показывает: истина живёт в карточках направлений, устремлений и дальше по цепочке. Собирается панелями по порядку.

## Колесо устремлений

```dataviewjs
const num = p => parseInt(String(p.id ?? "").match(/\d+/)?.[0]) || 999;
const title = p => (p.aliases ?? [])[0] ?? p.file.name;
const base = l => String(l?.path ?? l ?? "").split("/").pop().replace(/\.md$/, "");
const live = p => !p.file.folder.includes("archive");

const dirs = dv.pages('"10-governance/1-directions"').where(p => p.type === "direction" && live(p)).sort(num).array();
const asps = dv.pages('"10-governance/2-aspirations"').where(p => p.type === "aspiration" && live(p)).sort(num).array();
const sectors = dirs.map(d => ({ d, items: asps.filter(a => base(a.direction) === d.file.name) }));
const orphans = asps.filter(a => !dirs.some(d => base(a.direction) === d.file.name));
if (orphans.length) sectors.push({ d: null, items: orphans });

// A project names its parent itself (ADR-0040): `aspiration`, else `dissatisfaction` → its aspiration.
// Green = active and planned for the current sprint.
const many = v => [v ?? []].flat().filter(Boolean);
const index = (folder, type) => new Map(dv.pages(`"${folder}"`).where(p => String(p.type).startsWith(type)).array().map(p => [p.file.name, p]));
const diss = index("10-governance/3-dissatisfactions", "dissatisfaction");
const sprint = dv.pages('"10-governance/7-plans/current"').array().map(p => p.file.name.match(/^(.+)-sprintplan$/)?.[1]).find(Boolean);
const viaDis = links => links.map(l => diss.get(base(l))).filter(Boolean).flatMap(d => many(d.aspiration));
const projects = dv.pages('"10-governance/5-projects"').where(p => p.type === "project").sort(num).array().map(p => ({
  p,
  asps: new Set([
    many(p.aspiration),
    viaDis(many(p.dissatisfaction)),
  ].find(xs => xs.length)?.map(base)),
  now: p.status === "active" && !!sprint && String(p.period) === sprint,
}));
const loose = projects.filter(x => !asps.some(a => x.asps.has(a.file.name)));

const palette = ["--color-blue", "--color-purple", "--color-green", "--color-orange", "--color-red", "--color-cyan", "--color-yellow"];
const NS = "http://www.w3.org/2000/svg";
const el = (parent, tag, attrs = {}) => {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  parent.appendChild(e);
  return e;
};
const open = (p, ev) => app.workspace.openLinkText(p.file.path, "", ev.metaKey || ev.ctrlKey);
const hover = (p, ev, target) => app.workspace.trigger("hover-link", {
  event: ev, source: "preview", hoverParent: this.container, targetEl: target, linktext: p.file.path,
});

// One viewBox unit ≈ one screen pixel in a 700–760 px reading column, so font sizes are what the eye gets.
const FS = 15, FS_DIR = 16, LH = 1.25, WRAP = 180, WRAP_DIR = 110, GAP = 14;
const R_ME = 34, R_IN = 44, RX = 180, RY_MIN = 200, SIN_MAX = 0.93;
const ctx = document.createElement("canvas").getContext("2d"), FONT = getComputedStyle(document.body).fontFamily;
const measure = (s, size, weight = 400) => {
  ctx.font = `${weight} ${size}px ${FONT}`;
  return ctx.measureText(s).width;
};
// At most two lines, split at the word boundary that balances their widths; `tail` rides on the last line.
const wrap = (s, limit, size, weight, tail = 0) => {
  const words = s.split(" "), w = l => Math.max(...l.map((x, k) => measure(x, size, weight) + (k === l.length - 1 ? tail : 0)));
  if (w([s]) <= limit || words.length < 2) return [s];
  return words.slice(1).map((_, k) => [words.slice(0, k + 1).join(" "), words.slice(k + 1).join(" ")])
    .reduce((best, l) => w(l) < w(best) ? l : best);
};
const lines = (g, rows, x, y, size, anchor, attrs = {}) => {
  const t = el(g, "text", { x, y: y - (rows.length - 1) * size * LH / 2, "text-anchor": anchor, "dominant-baseline": "central", "font-size": size, fill: "var(--text-normal)", ...attrs });
  rows.forEach((row, k) => { el(t, "tspan", { x, dy: k ? size * LH : 0 }).textContent = row; });
  return t;
};

// Nodes run clockwise from the top: the first half down the right side, the rest up the left.
// Each side is stacked by label height, then every node is put on the rim at its row's height,
// so a label always sits level with its dot and never collides with a neighbour.
// Every label ends with two counts: projects taken into the current sprint (green) / all projects behind it.
const nodes = sectors.flatMap((s, i) => (s.items.length ? s.items : [null]).map(p => {
  if (!p) return { p, i, rows: [] };
  const all = projects.filter(x => x.asps.has(p.file.name)), now = all.filter(x => x.now);
  const tally = [String(now.length), `/${all.length}`], tail = 6 + measure(tally[0], FS, 700) + measure(tally[1], FS);
  return { p, i, all, now, tally, tail, rows: wrap(title(p), WRAP, FS, 400, tail) };
}));
const half = Math.ceil(nodes.length / 2);
const sides = [nodes.slice(0, half), nodes.slice(half).reverse()];
const height = n => Math.max(n.rows.length, 1) * FS * LH;
const need = Math.max(...sides.map(c => c.reduce((h, n) => h + height(n), 0) + GAP * (c.length - 1)));
const RY = Math.max(RY_MIN, need / 2 / SIN_MAX);
sides.forEach((col, side) => {
  if (!col.length) return;
  const sum = col.reduce((h, n) => h + height(n), 0);
  const gap = col.length > 1 ? (2 * RY * SIN_MAX - sum) / (col.length - 1) : 0;
  let y = col.length > 1 ? -RY * SIN_MAX : -height(col[0]) / 2;
  col.forEach(n => {
    n.y = y + height(n) / 2;
    y += height(n) + gap;
    const deg = Math.asin(n.y / RY) * 180 / Math.PI;
    n.t = side ? 180 - deg : deg;
    n.x = RX * Math.cos(n.t * Math.PI / 180);
    n.right = !side;
  });
});

const rim = deg => [RX * Math.cos(deg * Math.PI / 180), RY * Math.sin(deg * Math.PI / 180)];
const hub = deg => [R_IN * Math.cos(deg * Math.PI / 180), R_IN * Math.sin(deg * Math.PI / 180)];
const wedge = (a0, a1) => {
  const [x0, y0] = rim(a0), [x1, y1] = rim(a1), [x2, y2] = hub(a1), [x3, y3] = hub(a0);
  const big = a1 - a0 > 180 ? 1 : 0;
  return `M ${x0} ${y0} A ${RX} ${RY} 0 ${big} 1 ${x1} ${y1} L ${x2} ${y2} A ${R_IN} ${R_IN} 0 ${big} 0 ${x3} ${y3} Z`;
};
// Where the direction name fits inside its wedge: walk out from the middle of the wedge, then accept
// a tighter margin and a single line before giving up on a fit.
const spot = (d, a0, a1, name) => {
  const path = new Path2D(d), variants = [wrap(name, WRAP_DIR, FS_DIR, 700), [name]];
  const at = (f, da) => { const a = (a0 + a1) / 2 + da * (a1 - a0), [hx, hy] = hub(a), [ex, ey] = rim(a); return [hx + (ex - hx) * f, hy + (ey - hy) * f]; };
  const steps = (c, dx, n) => Array.from({ length: 2 * n + 1 }, (_, k) => c + dx * Math.ceil(k / 2) * (k % 2 ? -1 : 1));
  for (const pad of [10, 2]) for (const rows of variants) {
    const w = Math.max(...rows.map(r => measure(r, FS_DIR, 700))) / 2 + pad, h = rows.length * FS_DIR * LH / 2 + pad / 2;
    const inside = ([x, y]) => [-1, 0, 1].every(kx => [-1, 0, 1].every(ky => ctx.isPointInPath(path, x + kx * w, y + ky * h)));
    for (const f of steps(0.5, 0.06, 5)) for (const da of steps(0, 0.12, 3)) if (inside(at(f, da))) return [rows, ...at(f, da)];
  }
  return [variants[0], ...at(0.5, 0)];
};
const angle = k => nodes[(k + nodes.length) % nodes.length].t + 360 * Math.floor(k / nodes.length);

const svg = el(this.container, "svg", { width: "100%" });
const [under, over] = [el(svg, "g"), el(svg, "g")]; // direction names stay above every wedge edge
const bounds = [-RX, -RY, RX, RY];
sectors.forEach((s, i) => {
  const first = nodes.findIndex(n => n.i === i), last = nodes.findLastIndex(n => n.i === i);
  const a0 = (angle(first - 1) + angle(first)) / 2, a1 = Math.min((angle(last) + angle(last + 1)) / 2, a0 + 359.9);
  const color = `var(${palette[i % palette.length]})`;
  const g = el(under, "g");
  const band = el(g, "path", { d: wedge(a0, a1), fill: color, "fill-opacity": 0.16, stroke: "var(--background-primary)", "stroke-width": 3 });
  el(g, "path", { d: `M ${rim(a0).join(" ")} A ${RX} ${RY} 0 ${a1 - a0 > 180 ? 1 : 0} 1 ${rim(a1).join(" ")}`, fill: "none", stroke: color, "stroke-width": 4 });

  const [name, lx, ly] = spot(wedge(a0, a1), a0, a1, s.d ? title(s.d) : "⚠️ Без направления");
  const label = lines(over, name, lx, ly, FS_DIR, "middle", { "font-weight": 700 });
  if (s.d) {
    band.style.cursor = label.style.cursor = "pointer";
    band.addEventListener("click", ev => open(s.d, ev));
    label.addEventListener("click", ev => open(s.d, ev));
    label.addEventListener("mouseover", ev => hover(s.d, ev, label));
  }

  nodes.filter(n => n.i === i && n.p).forEach(n => {
    const node = el(g, "g");
    node.style.cursor = "pointer";
    const dot = el(node, "circle", { cx: n.x, cy: n.y, r: 7, fill: color, stroke: "var(--background-primary)", "stroke-width": 2 });
    const lx = n.x + (n.right ? 14 : -14);
    const text = lines(node, n.rows, lx, n.y, FS, n.right ? "start" : "end");
    const last = n.rows.length - 1, w = Math.max(...n.rows.map((r, k) => measure(r, FS) + (k === last ? n.tail : 0)));
    const names = xs => xs.map(x => title(x.p)).join("\n") || "—";
    const count = (x, anchor, s, attrs, tip) => {
      const c = el(g, "text", { x, y: n.y + last * FS * LH / 2, "text-anchor": anchor, "dominant-baseline": "central", "font-size": FS, ...attrs });
      c.textContent = s;
      el(c, "title").textContent = tip;
      return c;
    };
    const green = [{ fill: "var(--color-green)", "font-weight": 700, "fill-opacity": n.now.length ? 1 : 0.45 }, `В спринте ${sprint ?? "— спринт не открыт"}: ${n.now.length}\n${names(n.now)}`];
    const total = [{ fill: "var(--text-muted)" }, `Всего проектов: ${n.all.length}\n${names(n.all)}`];
    if (n.right) {
      const edge = lx + measure(n.rows[last], FS) + 6;
      count(edge, "start", n.tally[0], ...green);
      count(edge + measure(n.tally[0], FS, 700), "start", n.tally[1], ...total);
    } else {
      // Counts close the last line on this side too, so the line itself steps left to make room.
      text.lastChild.setAttribute("x", lx - n.tail);
      count(lx, "end", n.tally[1], ...total);
      count(lx - measure(n.tally[1], FS), "end", n.tally[0], ...green);
    }
    bounds[0] = Math.min(bounds[0], lx - (n.right ? 0 : w));
    bounds[2] = Math.max(bounds[2], lx + (n.right ? w : 0));
    bounds[1] = Math.min(bounds[1], n.y - height(n) / 2);
    bounds[3] = Math.max(bounds[3], n.y + height(n) / 2);
    node.addEventListener("click", ev => open(n.p, ev));
    node.addEventListener("mouseover", ev => { dot.setAttribute("r", 9); band.setAttribute("fill-opacity", 0.3); hover(n.p, ev, text); });
    node.addEventListener("mouseout", () => { dot.setAttribute("r", 7); band.setAttribute("fill-opacity", 0.16); });
  });
});

el(svg, "circle", { r: R_ME, fill: "var(--interactive-accent)" });
const me = el(svg, "g", { transform: `scale(${R_ME / 58})` });
el(me, "circle", { cx: 0, cy: -17, r: 14, fill: "var(--text-on-accent)" });
el(me, "path", { d: "M -27 30 C -27 8 -14 2 0 2 C 14 2 27 8 27 30 Z", fill: "var(--text-on-accent)" });

const [x0, y0, x1, y1] = bounds.map((b, k) => b + (k < 2 ? -8 : 8));
svg.setAttribute("viewBox", `${x0} ${y0} ${x1 - x0} ${y1 - y0}`);
svg.style.cssText = `max-width:${Math.ceil(x1 - x0)}px;display:block;margin:0 auto;font-family:var(--font-interface);`;

// Projects that trace to no live aspiration stay visible under the wheel instead of vanishing from the counts.
if (loose.length) {
  const note = this.container.appendChild(document.createElement("div"));
  note.style.cssText = `max-width:${Math.ceil(x1 - x0)}px;margin:6px auto 0;font-size:13px;line-height:1.5;color:var(--text-muted);`;
  note.append(`Без устремления: ${loose.length} — `);
  loose.forEach((x, k) => {
    const link = note.appendChild(document.createElement("span"));
    link.textContent = title(x.p);
    link.title = `статус: ${x.p.status ?? "—"}`;
    link.style.cssText = `cursor:pointer;color:var(${x.p.status === "active" ? "--text-normal" : "--text-muted"});`;
    link.addEventListener("click", ev => open(x.p, ev));
    link.addEventListener("mouseover", ev => hover(x.p, ev, link));
    if (k < loose.length - 1) note.append(" · ");
  });
}
```

## Долгосрочное видение

```dataviewjs
const num = p => parseInt(String(p.id ?? "").match(/\d+/)?.[0]) || 999;
const title = p => (p.aliases ?? [])[0] ?? p.file.name;
const base = l => String(l?.path ?? l ?? "").split("/").pop().replace(/\.md$/, "");
const live = p => !p.file.folder.includes("archive");

// Wheel order and colours: directions by id, each aspiration in its direction's palette slot.
const palette = ["--color-blue", "--color-purple", "--color-green", "--color-orange", "--color-red", "--color-cyan", "--color-yellow"];
const dirs = dv.pages('"10-governance/1-directions"').where(p => p.type === "direction" && live(p)).sort(num).array();
const slot = a => { const k = dirs.findIndex(d => d.file.name === base(a.direction)); return k < 0 ? dirs.length : k; };
const asps = dv.pages('"10-governance/2-aspirations"').where(p => p.type === "aspiration" && live(p)).array()
  .sort((a, b) => slot(a) - slot(b) || num(a) - num(b));
const vision = a => String(a.vision ?? "").trim();

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

const list = h(this.container, "div", "display:flex;flex-direction:column;gap:4px;line-height:1.45;");
asps.filter(vision).forEach(a => {
  // An agent's draft stays visibly provisional until the owner approves it by dropping `vision_status`.
  const draft = a.vision_status === "draft";
  const item = h(list, "div", "padding-left:14px;text-indent:-14px;");
  h(item, "span", `display:inline-block;width:7px;height:7px;margin-right:7px;border-radius:50%;vertical-align:1px;text-indent:0;background:var(${palette[slot(a) % palette.length]});`);
  link(h(item, "span", "font-weight:600;", title(a)), a);
  if (draft) h(item, "span", "margin-left:6px;padding:0 5px;border:1px dashed var(--background-modifier-border);border-radius:4px;font-size:11.5px;color:var(--text-muted);white-space:nowrap;", "черновик агента");
  item.append(" — ");
  h(item, "span", draft ? "font-style:italic;color:var(--text-muted);" : "", vision(a));
});
const blank = asps.filter(a => !vision(a));
if (blank.length) h(list, "div", "margin-top:2px;font-size:13px;color:var(--text-muted);", `видение не записано у ${blank.length} устремлений`).title = blank.map(title).join("\n");
```

## Текущие неудовлетворённости

```dataviewjs
const num = p => parseInt(String(p.id ?? "").match(/\d+/)?.[0]) || 999;
const title = p => (p.aliases ?? [])[0] ?? p.file.name;
const base = l => String(l?.path ?? l ?? "").split("/").pop().replace(/\.md$/, "");
const live = p => !p.file.folder.includes("archive");
const many = v => [v ?? []].flat().filter(Boolean);

// Colours follow the wheel above: a direction's palette slot is its rank among live directions, orphans take the next.
const palette = ["--color-blue", "--color-purple", "--color-green", "--color-orange", "--color-red", "--color-cyan", "--color-yellow"];
const dirs = dv.pages('"10-governance/1-directions"').where(p => p.type === "direction" && live(p)).sort(num).array();
const asps = new Map(dv.pages('"10-governance/2-aspirations"').where(p => p.type === "aspiration" && live(p)).array().map(a => [a.file.name, a]));
const tint = a => {
  const k = dirs.findIndex(d => d.file.name === base(a.direction));
  return `var(${palette[(k < 0 ? dirs.length : k) % palette.length]})`;
};
const sprint = dv.pages('"10-governance/7-plans/current"').array().map(p => p.file.name.match(/^(.+)-sprintplan$/)?.[1]).find(Boolean);
const projects = dv.pages('"10-governance/5-projects"').where(p => p.type === "project").sort(num).array();
const STATUS = { active: "идёт", done: "завершён", archived: "в архиве", merged: "слит", incubation: "бэклог" };

// A card whose only alias is its id is named by its H1, minus the "DIS-N —" prefix.
const name = p => {
  if (title(p) !== p.id) return title(p);
  const h1 = app.metadataCache.getCache(p.file.path)?.headings?.find(h => h.level === 1)?.heading ?? "";
  return h1.replace(new RegExp(`^${p.id}\\s*[—–-]\\s*`), "") || p.file.name;
};
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
const line = "display:flex;align-items:center;gap:6px;font-size:13px;min-width:0;";
const clip = "flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;";

// Sprint work first, then dissatisfactions with any live project, then the unattended ones.
const cards = dv.pages('"10-governance/3-dissatisfactions"').where(p => p.type === "dissatisfaction" && p.status === "active" && live(p)).array()
  .map(d => {
    const own = projects.filter(p => many(p.dissatisfaction).some(l => base(l) === d.file.name))
      .map(p => ({ p, now: p.status === "active" && !!sprint && String(p.period) === sprint }));
    return { d, own, rank: own.some(x => x.now) ? 0 : own.some(x => x.p.status === "active") ? 1 : 2 };
  })
  .sort((a, b) => a.rank - b.rank || num(a.d) - num(b.d));

// Three cards a row in a 700–800 px pane; the column floor drops it to two, then one, below ~520 px.
const grid = h(this.container, "div", "display:grid;grid-template-columns:repeat(auto-fill,minmax(max(166px,calc((100% - 20px) / 3)),1fr));gap:10px;");
cards.forEach(({ d, own }) => {
  const asp = asps.get(base(d.aspiration)), color = asp ? tint(asp) : "var(--text-faint)";
  const card = h(grid, "div", `display:flex;flex-direction:column;gap:5px;min-width:0;padding:8px 10px;border-radius:6px;line-height:1.35;color:var(--text-normal);background:var(--background-secondary);border:1px solid var(--background-modifier-border);border-left:3px solid ${color};`);

  const head = h(card, "div", "font-size:13.5px;");
  link(h(head, "span", "font-weight:600;", name(d)), d);
  head.append(" ");
  h(head, "span", "font-size:12px;color:var(--text-muted);white-space:nowrap;", d.id);
  head.append(" ");
  if (d.driver_type) h(head, "span", "padding:0 5px;border:1px solid var(--background-modifier-border);border-radius:4px;font-size:11.5px;color:var(--text-muted);white-space:nowrap;", d.driver_type);
  if (d.driver) h(card, "div", "font-size:13px;color:var(--text-muted);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;", d.driver).title = d.driver;

  const aspLine = h(card, "div", line);
  h(aspLine, "span", dot(color));
  if (asp) link(h(aspLine, "span", `${clip}color:var(--text-normal);`, title(asp)), asp).title = title(asp);
  else h(aspLine, "span", `${clip}color:var(--text-muted);`, "устремление не указано");

  if (!own.length) h(card, "div", "font-size:13px;color:var(--text-muted);", "проекта нет");
  // A green dot is the sprint mark, as on the wheel; other projects say their status instead.
  own.forEach(({ p, now }) => {
    const row = h(card, "div", `${line}${p.status === "incubation" ? "opacity:0.55;" : ""}`);
    h(row, "span", now ? dot("var(--color-green)") : `${dot("transparent")}box-shadow:inset 0 0 0 1.5px var(--text-faint);`);
    link(h(row, "span", clip, title(p)), p).title = `${title(p)} — ${now ? `спринт ${sprint}` : STATUS[p.status] ?? p.status ?? "—"}`;
    if (!now) h(row, "span", "flex:none;font-size:12px;color:var(--text-muted);", STATUS[p.status] ?? p.status ?? "—");
  });
});
```

## Проекты

```dataviewjs
const num = p => parseInt(String(p.id ?? "").match(/\d+/)?.[0]) || 999;
const title = p => (p.aliases ?? [])[0] ?? p.file.name;
const base = l => String(l?.path ?? l ?? "").split("/").pop().replace(/\.md$/, "");
const live = p => !p.file.folder.includes("archive");
const many = v => [v ?? []].flat().filter(Boolean);
const byName = (folder, type) => new Map(dv.pages(`"${folder}"`).where(p => String(p.type).startsWith(type)).array().map(p => [p.file.name, p]));

// Colours follow the wheel: a direction's palette slot is its rank among live directions, orphans take the next.
const palette = ["--color-blue", "--color-purple", "--color-green", "--color-orange", "--color-red", "--color-cyan", "--color-yellow"];
const dirs = dv.pages('"10-governance/1-directions"').where(p => p.type === "direction" && live(p)).sort(num).array();
const asps = new Map(dv.pages('"10-governance/2-aspirations"').where(p => p.type === "aspiration" && live(p)).array().map(a => [a.file.name, a]));
const tint = a => {
  const k = dirs.findIndex(d => d.file.name === base(a.direction));
  return `var(${palette[(k < 0 ? dirs.length : k) % palette.length]})`;
};
const diss = byName("10-governance/3-dissatisfactions", "dissatisfaction");
const sprint = dv.pages('"10-governance/7-plans/current"').array().map(p => p.file.name.match(/^(.+)-sprintplan$/)?.[1]).find(Boolean);
const STATUS = { active: "идёт", done: "завершён", incubation: "инкубация", archived: "в архиве", merged: "слит" };
const FINISHED = ["done", "merged", "archived", "closed", "dropped"];

// A card whose only alias is its id is named by its H1, minus the "DIS-N —" prefix.
const name = p => {
  if (title(p) !== p.id) return title(p);
  const h1 = app.metadataCache.getCache(p.file.path)?.headings?.find(h => h.level === 1)?.heading ?? "";
  return h1.replace(new RegExp(`^${p.id}\\s*[—–-]\\s*`), "") || p.file.name;
};
const h = (parent, tag, css, text) => {
  const e = parent.appendChild(document.createElement(tag));
  e.style.cssText = css;
  if (text != null) e.textContent = text;
  return e;
};
const link = (e, p) => {
  e.style.cursor = "pointer";
  e.title = name(p);
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
const badge = "padding:0 5px;border:1px solid var(--background-modifier-border);border-radius:4px;font-size:11.5px;color:var(--text-muted);white-space:nowrap;";

// Parent per ADR-0040: own `aspiration`, else `dissatisfaction`.
const cards = dv.pages('"10-governance/5-projects"').where(p => p.type === "project" && !FINISHED.includes(String(p.status))).array().map(p => {
  const ds = many(p.dissatisfaction).map(l => diss.get(base(l))).filter(Boolean);
  const own = many(p.aspiration).map(l => asps.get(base(l))).filter(Boolean);
  const via = [...new Set(ds.flatMap(d => many(d.aspiration)).map(base))].map(n => asps.get(n)).filter(Boolean);
  const now = p.status === "active" && !!sprint && String(p.period) === sprint;
  const rank = now ? 0 : p.status === "active" ? 1 : 2;
  return { p, ds, aims: own.length ? own : via, direct: own.length > 0, now, rank };
}).sort((a, b) => a.rank - b.rank || (a.p.priority ?? 99) - (b.p.priority ?? 99) || num(a.p) - num(b.p));

// Three tiers, each under its own small heading: the sprint stands out, the rest of the live work is plain,
// and the backlog recedes until hovered.
const TIERS = [
  [`В спринте ${sprint ?? ""}`, "background:color-mix(in srgb, var(--color-green) 8%, var(--background-secondary));border:1px solid color-mix(in srgb, var(--color-green) 45%, var(--background-modifier-border));"],
  ["Активные вне спринта", "background:var(--background-secondary);border:1px solid var(--background-modifier-border);"],
  ["Бэклог", "background:transparent;border:1px dashed var(--background-modifier-border);opacity:0.55;"],
];
const grids = TIERS.map(([label], rank) => {
  const n = cards.filter(c => c.rank === rank).length;
  if (!n) return null;
  h(this.container, "div", `margin:${rank ? 16 : 4}px 0 6px;font-size:13px;font-weight:600;color:var(--text-muted);`, `${label} · ${n}`);
  return h(this.container, "div", "display:grid;grid-template-columns:repeat(auto-fill,minmax(max(166px,calc((100% - 20px) / 3)),1fr));gap:10px;");
});
cards.forEach(({ p, ds, aims, direct, now, rank }) => {
  const color = aims.length ? tint(aims[0]) : "var(--text-faint)";
  const card = h(grids[rank], "div", `display:flex;flex-direction:column;gap:5px;min-width:0;padding:8px 10px;border-radius:6px;line-height:1.35;color:var(--text-normal);transition:opacity .15s;${TIERS[rank][1]}border-left:3px ${rank === 2 ? "dashed" : "solid"} ${color};`);
  if (rank === 2) {
    card.addEventListener("mouseenter", () => { card.style.opacity = 1; });
    card.addEventListener("mouseleave", () => { card.style.opacity = 0.55; });
  }

  const head = h(card, "div", "font-size:13.5px;");
  if (now) h(head, "span", `${dot("var(--color-green)")}margin-right:6px;vertical-align:1px;`);
  link(h(head, "span", "font-weight:600;", title(p)), p);
  for (const [text, css] of [
    [p.id, "font-size:12px;color:var(--text-muted);white-space:nowrap;"],
    [now && p.priority != null ? `№${p.priority}` : null, badge],
    [rank === 2 ? "бэклог" : STATUS[p.status] ?? p.status, badge],
    [p.budget_h != null ? `${p.budget_h} ч` : null, badge],
  ]) if (text) { head.append(" "); h(head, "span", css, text); }
  if (p.criterion) h(card, "div", "font-size:13px;color:var(--text-muted);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;", p.criterion).title = p.criterion;

  const disLine = h(card, "div", line);
  h(disLine, "span", ring);
  if (ds.length) link(h(disLine, "span", clip, name(ds[0])), ds[0]);
  if (ds.length > 1) h(disLine, "span", "flex:none;font-size:12px;color:var(--text-muted);", `+${ds.length - 1}`).title = ds.slice(1).map(name).join("\n");
  if (!ds.length) h(disLine, "span", `${clip}color:var(--text-muted);`, direct ? "напрямую от устремления" : "без неудовлетворённости");

  const aimLine = h(card, "div", line);
  h(aimLine, "span", dot(color));
  if (aims.length) link(h(aimLine, "span", clip, title(aims[0]) + (aims.length > 1 ? ` +${aims.length - 1}` : "")), aims[0]);
  else h(aimLine, "span", `${clip}color:var(--text-muted);`, "без устремления");
});
```

## Незавершённые задачи

```dataviewjs
const num = p => parseInt(String(p.id ?? "").match(/\d+/)?.[0]) || 999;
const base = l => String(l?.path ?? l ?? "").split("/").pop().replace(/\.md$/, "");
const live = p => !p.file.folder.includes("archive");
const many = v => [v ?? []].flat().filter(Boolean);
const planId = kind => dv.pages('"10-governance/7-plans/current"').array()
  .map(p => p.file.name.match(new RegExp(`^(.+)-${kind}$`))?.[1]).filter(Boolean).sort().pop();
const sprint = planId("sprintplan"), unit = planId("unitplan");
const DONE = ["done", "closed", "dropped"], FINISHED = ["done", "merged", "archived", "closed", "dropped"];
const STATUS = { "in-progress": "в работе", blocked: "заблокирована", later: "позже" };

// A card named only by its id (or not at all) is named by its H1, minus the "T-NNN —" prefix.
const name = p => {
  const alias = (p.aliases ?? [])[0];
  if (alias && alias !== p.id) return alias;
  const h1 = app.metadataCache.getCache(p.file.path)?.headings?.find(h => h.level === 1)?.heading ?? "";
  return h1.replace(new RegExp(`^${p.id}\\s*[—–-]\\s*`), "") || p.file.name;
};
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
const badge = "flex:none;padding:0 5px;border:1px solid var(--background-modifier-border);border-radius:4px;font-size:11.5px;color:var(--text-muted);white-space:nowrap;";
const hours = x => String(Math.round(x * 10) / 10).replace(".", ",");

// Owner's rule: sprint projects by priority, then other active ones, then the backlog, then the finished;
// inside a project, the current unit's tasks first, then work in progress, then `later`.
const projects = new Map(dv.pages('"10-governance/5-projects"').where(p => p.type === "project").array().map(p => [p.file.name, p]));
const tier = p => !p ? 4 : FINISHED.includes(String(p.status)) ? 3
  : p.status !== "active" ? 2 : sprint && String(p.period) === sprint ? 0 : 1;
const step = t => unit && String(t.unit) === unit ? 0 : t.status === "later" ? 2 : 1;
const groups = new Map();
dv.pages('"10-governance/6-tasks"').where(t => t.type === "task" && live(t) && !DONE.includes(String(t.status))).array()
  .forEach(t => {
    const p = projects.get(base(many(t.project)[0])) ?? null, key = p?.file.name ?? "";
    if (!groups.has(key)) groups.set(key, { p, tasks: [] });
    groups.get(key).tasks.push(t);
  });
const ordered = [...groups.values()].sort((a, b) => tier(a.p) - tier(b.p)
  || (a.p?.priority ?? 99) - (b.p?.priority ?? 99) || num(a.p ?? {}) - num(b.p ?? {}));

const list = h(this.container, "div", "display:flex;flex-direction:column;gap:12px;");
ordered.forEach(({ p, tasks }) => {
  const group = h(list, "div", tier(p) >= 2 ? "opacity:0.6;" : "");
  const head = h(group, "div", "margin-bottom:4px;font-size:13.5px;font-weight:600;line-height:1.35;");
  if (tier(p) === 0) h(head, "span", "display:inline-block;width:7px;height:7px;margin-right:8px;border-radius:50%;vertical-align:1px;background:var(--color-green);");
  if (p) link(h(head, "span", "", (p.aliases ?? [])[0] ?? p.file.name), p);
  else h(head, "span", "color:var(--text-muted);", "Без проекта");
  if (p && tier(p) === 0 && p.priority != null) h(head, "span", "margin-left:8px;font-size:12px;font-weight:400;color:var(--text-muted);white-space:nowrap;", `№${p.priority}`);
  if (p && tier(p) >= 2) h(head, "span", `${badge}margin-left:8px;font-weight:400;`, tier(p) === 2 ? "бэклог" : { archived: "в архиве", merged: "слит" }[p.status] ?? "завершён");

  tasks.sort((a, b) => step(a) - step(b) || num(a) - num(b)).forEach(t => {
    const later = step(t) === 2 && tier(p) < 2; // a receded group is dimmed once, not twice
    const row = h(group, "div", `display:flex;align-items:baseline;gap:8px;min-width:0;padding:3px 0 3px 15px;font-size:13.5px;border-top:1px solid var(--background-modifier-border);${later ? "opacity:0.55;" : ""}`);
    if (later) {
      row.addEventListener("mouseenter", () => { row.style.opacity = 1; });
      row.addEventListener("mouseleave", () => { row.style.opacity = 0.55; });
    }
    link(h(row, "span", "flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;", name(t)), t).title = name(t);
    h(row, "span", "flex:none;font-size:12px;color:var(--text-muted);", t.id);
    if (step(t) === 0) h(row, "span", `${badge}color:var(--text-normal);border-color:var(--interactive-accent);`, "юнит");
    h(row, "span", badge, STATUS[t.status] ?? t.status ?? "—");
    const budget = Number(t.budget_h) || 0;
    h(row, "span", "flex:none;width:92px;text-align:right;font-size:12px;color:var(--text-muted);white-space:nowrap;",
      budget ? `ост. ${hours(budget - (Number(t.spent_h) || 0))} из ${hours(budget)} ч` : "—");
  });
});
```
