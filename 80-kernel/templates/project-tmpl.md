<%*
// Проект = папка PNN-slug с одноимённой карточкой внутри (ADR-0006).
// Номер: max существующих + 1 (не count — архивированные проекты оставляют дыры,
// но не должны давать коллизий: номер архивного проекта не переиспользуется).
let _mx = 0;
for (const f of app.vault.getMarkdownFiles()) {
    const m = f.basename.match(/^P(\d+)-/);
    if (m) _mx = Math.max(_mx, parseInt(m[1], 10));
}
const pnum = await tp.system.prompt("P-номер (сверься и с Super Productivity — карточка может лежать незакоммиченной на второй машине, ADR-0031):", "P" + (_mx + 1));
const slug = await tp.system.prompt("Английский slug:");
const ruTitle = await tp.system.prompt("Русское название — результатом, из которого видна цель (ADR-0040):");

// Проект и есть цель (ADR-0040): имя — результат, из которого цель видна без пояснений.
// Родитель один — главная неудовлетворённость; где боли нет — устремление напрямую.
const _basenames = (dir) => app.vault.getMarkdownFiles()
    .filter(f => f.parent && f.parent.path === dir)
    .map(f => f.basename)
    .sort();

const _dis = _basenames("10-governance/3-dissatisfactions").filter(d => /^DIS-\d+-/.test(d));
const _asp = _basenames("10-governance/2-aspirations").filter(a => /^ASP-\d+-/.test(a));
const parent = await tp.system.suggester(
    _dis.map(d => "DIS · " + d).concat(_asp.map(a => "ASP · " + a)),
    _dis.map(d => ["dissatisfaction", d]).concat(_asp.map(a => ["aspiration", a])),
    false, "Родитель проекта (неудовлетворённость; устремление — только где боли нет):");
const parentLine = `${parent[0]}: "[[${parent[1]}]]"`;

const scope = await tp.system.suggester(
    ["finite — проект-цель: есть критерий достижения", "infinite — русло/политика, не завершается"],
    ["finite", "infinite"], false, "Род проекта:");
const period = scope === "finite" ? await tp.system.prompt("Спринт, в котором проект взят (period):", "YYYY-sN") : null;

const folder = `10-governance/5-projects/${pnum}-${slug}`;
await tp.file.move(`${folder}/${pnum}-${slug}`);

// Зеркало в приборе учёта (ADR-0031). Templater до SP не дотягивается, поэтому
// напоминание, а не действие: забывается именно эта половина — она вне Obsidian.
await tp.system.suggester(
    [`✔ Завёл в Super Productivity: ${pnum} — ${ruTitle}`,
     "✗ Позже — номер занят, зеркала нет, время списывать некуда"],
    ["ok", "later"], false,
    "Зеркало в приборе учёта (ADR-0031):");
-%>
---
type: project
id: <% pnum %>
<% parentLine %>
<%* tR += period ? `period: ${period}
criterion: "<наблюдаемый критерий достижения>"
budget_h: 
` : "" %>scope: <% scope %>
status: active
aliases: ["<% ruTitle %>", "<% pnum %>"]
valid_from: <% tp.date.now("YYYY-MM-DD") %>
---

# <% pnum %> — <% ruTitle %>

<%* tR += scope === "finite"
    ? "Проект-цель (`scope: finite`): <к какому исходу ведёт; имя проекта и есть этот исход>. Завершается достижением `criterion`."
    : "Бесконечный проект (`scope: infinite`): <какое русло держит>. Завершаются отдельные задачи, не проект." %>

<%* tR += `**Трассировка:** [[${parent[1]}]] → ${pnum}. Выше по цепочке — устремление и направление; полями здесь не дублируются (ADR-0040).`
    + (scope === "finite" ? "" : " Бессрочное русло критерия не имеет: задача, взятая в юнит под него, краснеет в детекторе (ADR-0040 п.5).") %>

> **Почему проект, а не задача.** <многие включения разного рода · нет формулируемого критерия готовности одного артефакта>

## Задачи проекта

```dataview
TABLE status, phase FROM "10-governance/6-tasks" WHERE project = this.file.link SORT status
```

<%* tR += scope === "finite" ? `## Критерий достижения

- [ ] <исход 1 — предъявимый, а не «поработал»>
- [ ] <исход 2>` : `## Состав работ

- <какие роды работ идут в этом русле; сложенные в одну задачу — вырождаются>` %>
