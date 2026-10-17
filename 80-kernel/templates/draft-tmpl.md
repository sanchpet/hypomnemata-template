<%*
// Номер = max существующих d-NNN + 1 (не count: удаления оставляют дыры,
// но не должны давать коллизий — тот же приём, что в learn-note-tmpl).
let _mx = 0;
for (const f of app.vault.getMarkdownFiles()) {
    const m = f.basename.match(/^d-(\d+)(?:-|$)/);
    if (m) _mx = Math.max(_mx, parseInt(m[1], 10));
}
const _id = "d-" + String(_mx + 1).padStart(3, "0");

const ruTitle = await tp.system.prompt("Тема (рус.):");
const _alias = String(ruTitle || "").replace(/\\/g, "\\\\").replace(/"/g, '\\"');

// Имя файла — латиницей (ADR-0006), и владелец его не набирает: slug выводится
// из темы транслитерацией. Человекочитаемость даёт alias, не имя.
const _map = {
    а:"a", б:"b", в:"v", г:"g", д:"d", е:"e", ё:"e", ж:"zh", з:"z", и:"i",
    й:"y", к:"k", л:"l", м:"m", н:"n", о:"o", п:"p", р:"r", с:"s", т:"t",
    у:"u", ф:"f", х:"h", ц:"ts", ч:"ch", ш:"sh", щ:"sch", ъ:"", ы:"y", ь:"",
    э:"e", ю:"yu", я:"ya"
};
let _slug = String(ruTitle || "").toLowerCase()
    .split("").map(c => (c in _map) ? _map[c] : c).join("")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
// Длинное имя режется по границе слова: обрубок посреди слова хуже короткого.
if (_slug.length > 50) {
    _slug = _slug.slice(0, 50).replace(/-[^-]*$/, "");
}

// Устремление обязательно: без него не о чем и писать. Отмену спрашиваем
// второй раз, а не по кругу — иначе из шаблона не выйти.
const _asps = app.vault.getMarkdownFiles()
    .filter(f => f.parent && f.parent.path === "10-governance/2-aspirations" && /^ASP-\d+-/.test(f.basename))
    .map(f => {
        const fm = app.metadataCache.getFileCache(f)?.frontmatter ?? {};
        return { name: f.basename, n: parseInt(f.basename.match(/^ASP-(\d+)/)[1], 10), label: [fm.aliases ?? []].flat()[0] ?? f.basename };
    })
    .sort((a, b) => a.n - b.n);
let _asp = null;
for (const ask of ["Устремление черновика:", "Без устремления не о чем писать — выбери устремление:"]) {
    _asp = await tp.system.suggester(_asps.map(a => `ASP-${a.n} · ${a.label}`), _asps.map(a => a.name), false, ask);
    if (_asp) break;
}
const _aspLink = _asp ? "[[" + _asp + "]]" : "";

await tp.file.move("20-library/drafts/" + _id + (_slug ? "-" + _slug : ""));
-%>
---
type: draft
id: <% _id %>
aliases: ["<% _alias %>"]
created: <% tp.date.now("YYYY-MM-DD") %>
aspiration: "<% _aspLink %>"
projects: []
priority:
---

# <% ruTitle %>

```dataviewjs
// Масса и правило приоритета — копия модуля 20-library/pipeline/views/drafts-panel.js (источник правила,
// панель «Черновики» модели и старта): правило меняется там, затем здесь — шапка одного черновика не зовёт модуль.
// Масса — сколько входов впало в черновик: входящие ссылки со страниц-входов конвейера.
const KINDS = [["learn-note", "заметки"], ["finding", "находки"], ["conversation", "беседы"], ["journal", "дневник"]];
const CLOSED = ["done", "closed", "archived", "merged"];
const cur = dv.current();
const pageOf = l => l ? dv.page(l.path ?? String(l)) : null;
const name = p => [p.aliases ?? []].flat()[0] ?? p.file.name;
const ref = p => String(dv.fileLink(p.file.path, false, name(p)));
const rank = v => { const n = Number(v); return Number.isInteger(n) && n > 0 ? n : null; };

const per = KINDS.map(([type, label]) => [label, cur.file.inlinks.filter(l => pageOf(l)?.type === type).length]).filter(([, n]) => n);
const mass = per.reduce((s, [, n]) => s + n, 0);

const asp = pageOf(cur.aspiration);
const projects = [cur.projects ?? []].flat().map(pageOf).filter(Boolean);
const live = p => !p.file.folder.includes("archive") && !CLOSED.includes(String(p.status ?? "").toLowerCase());
const lead = projects.filter(live).map(p => ({ p, r: rank(p.priority) ?? Infinity })).sort((a, b) => a.r - b.r)[0];

const own = rank(cur.priority);
const prio = cur.file.folder.includes("archive") ? "архив"
  : own ? `№${own}`
  : lead ? `↑ ${lead.p.id ?? lead.p.file.name}${lead.r < Infinity ? ` №${lead.r}` : ""}`
  : "прочие, по массе";

this.container.style.cssText += "font-size:13px;color:var(--text-muted);";
dv.paragraph([
  mass ? `масса ${mass}: ${per.map(([l, n]) => `${l} ${n}`).join(" · ")}` : "масса: пока пусто",
  `приоритет: ${prio}`,
].join(" · ") + "<br>" + [
  asp ? `устремление: ${ref(asp)}` : "**устремление не указано**",
  projects.length ? `проекты: ${projects.map(p => `${ref(p)}${!live(p) ? " (закрыт)" : rank(p.priority) ? " №" + rank(p.priority) : ""}`).join(", ")}` : "проектов нет",
].join(" · "));
```
<%* if (!_asp) { -%>

> [!warning] Устремление не выбрано
> Черновик без устремления не о чем писать. Впиши `aspiration:` во frontmatter — wikilink на карточку `10-governance/2-aspirations/ASP-*`.
<%* } -%>

## Идеи

-

## Откуда пришло

-
