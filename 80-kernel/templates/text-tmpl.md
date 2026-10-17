<%*
// Текст пишется отдельным файлом из черновика: род — папкой, домен и черновик — свойствами.
const ruTitle = await tp.system.prompt("Текст (рус.):");

const kind = await tp.system.suggester(
    ["Датированный — привязан к моменту, не меняется", "Вечнозелёный — растёт редакциями"],
    ["post", "evergreen"], false, "Род текста");
const _kind = kind || "post";

// Домены и каналы публикации — ваши (ADR-0012: перечень каналов принадлежит владельцу).
// HOME — канал по умолчанию для домена; прочие каналы дописываются в `channels` руками.
const DOMAINS = { general: "Общий", engineering: "Инженерный" };
const domain = await tp.system.suggester(Object.values(DOMAINS), Object.keys(DOMAINS), false, "Домен") || "general";
const HOME = { general: "channel-1", engineering: "channel-2" };

// Начат из черновика — он и есть источник; иначе выбрать из активных.
const _active = app.workspace.getActiveFile();
const _isDraft = f => f && f.path.startsWith("20-library/drafts/") && !f.path.startsWith("20-library/drafts/archive/");
let source = _isDraft(_active) ? _active : null;
if (!source) {
    const drafts = app.vault.getMarkdownFiles().filter(_isDraft).sort((a, b) => a.basename.localeCompare(b.basename));
    const label = f => {
        const fm = app.metadataCache.getFileCache(f)?.frontmatter;
        return f.basename.slice(0, 5) + " · " + ((fm?.aliases ?? [])[0] ?? f.basename);
    };
    source = await tp.system.suggester(["— без черновика (в серию не идёт)", ...drafts.map(label)], [null, ...drafts], false, "Черновик-источник");
}
const _drafts = source ? `["[[${source.basename}]]"]` : "[]";

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
if (_slug.length > 50) _slug = _slug.slice(0, 50).replace(/-[^-]*$/, "");
const _folder = _kind === "evergreen" ? "20-library/evergreen/" : "20-library/posts/";
await tp.file.move(_folder + (_slug || "text-" + tp.date.now("YYYYMMDD-HHmm")));
const _alias = String(ruTitle || "").replace(/\\/g, "\\\\").replace(/"/g, '\\"');
-%>
---
type: <% _kind %>
aliases: ["<% _alias %>"]
domain: <% domain %>
<%* if (_kind === "post") { -%>
channels: [<% HOME[domain] %>]
<%* } -%>
drafts: <% _drafts %>
created: <% tp.date.now("YYYY-MM-DD") %>
---

# <% ruTitle %>

> Планка: одна мысль, таймбокс; вышло по времени — публикуется, можно с пометкой «рабочий вариант». При публикации — <%* tR += _kind === "post" ? "`published` и `link`" : "`revised` и `revision`" %>.

<% tp.file.cursor(1) %>
