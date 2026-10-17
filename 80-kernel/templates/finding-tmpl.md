<%*
const ruTitle = await tp.system.prompt("Находка (рус.):");

// Транслитерация — как в draft-tmpl: имя латиницей (ADR-0006), смысл в alias.
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
if (_slug.length > 50) {
    _slug = _slug.slice(0, 50).replace(/-[^-]*$/, "");
}
// Находка живёт в лотке до разбора (вход EN-4 конвейера); перенос в 9-notes — на разборе.
await tp.file.move("00-inbox/findings/" + (_slug || "finding-" + tp.date.now("YYYYMMDD-HHmm")));
-%>
---
type: finding
writer: mixed
aliases: ["<% ruTitle %>"]
created: <% tp.date.now("YYYY-MM-DD") %>
drafts: []
---

# <% ruTitle %>

> С работы на работодателя — только обезличенно: класс задачи, без имён, хостов и деталей системы.

<% tp.file.cursor(1) %>
