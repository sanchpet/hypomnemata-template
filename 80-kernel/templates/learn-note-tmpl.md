<%*
// Источник = активная карточка (курс/книга/гайд), на которой создаётся заметка.
const _src = app.workspace.getActiveFile();
const _srcFolders = ["20-library/resources/1-books","20-library/resources/2-courses","20-library/resources/3-guides","20-library/resources/4-sources"];
const _cache = _src ? app.metadataCache.getFileCache(_src) : null;
const _isSource = _src && _src.parent && _srcFolders.includes(_src.parent.path);

// R-id источника → slug-префикс имени: "R-001" → "r001".
const _srcId = (_isSource && _cache && _cache.frontmatter && _cache.frontmatter.id)
    ? String(_cache.frontmatter.id).toLowerCase().replace(/[^a-z0-9]/g, "")
    : null;

// Свойства источника для суффикса alias (ADR-0025): R-id, род→эмодзи, short, provider.
// Род берётся из свойства `type` карточки (НЕ из папки — ФС ненадёжен, INV-1).
const _fm = (_isSource && _cache && _cache.frontmatter) ? _cache.frontmatter : {};
const _srcIdRaw = _fm.id ? String(_fm.id) : null;
const _emojiByType = { course: "🎓", book: "📖", guide: "🛠️", source: "🌐" };
const _emoji = _emojiByType[_fm.type] || "";
const _short = _fm.short ? String(_fm.short) : null;
const _provider = _fm.provider ? String(_fm.provider) : null;

// Ссылка на карточку-источник (замена QuickAdd-переменной {{LINKCURRENT}}).
const _srcLink = _src ? "[[" + _src.basename + "]]" : "";

// Имя файла = <источник>-<номер>, номер = max существующих + 1 (а не count —
// удаления оставляют дыры, но не дают коллизий). Без источника → timestamp-fallback.
let _fname;
if (_srcId) {
    const _re = new RegExp("^" + _srcId + "-(\\d+)$");
    let _mx = 0;
    for (const f of app.vault.getMarkdownFiles()) {
        const m = f.basename.match(_re);
        if (m) _mx = Math.max(_mx, parseInt(m[1], 10));
    }
    _fname = _srcId + "-" + String(_mx + 1).padStart(2, "0");
} else {
    _fname = "note-" + tp.date.now("YYYYMMDDHHmmss");
}

// Тема (рус., с пробелами) → alias. Теги наследуются от карточки-источника.
const ruTitle = await tp.system.prompt("Тема заметки (рус.):");
// Alias = «Тема (эмодзи short @provider · R-id)» (ADR-0025); @provider и · R-id
// опускаются при отсутствии; нет short (не-источник) → голая тема.
let _alias = ruTitle;
if (_short) {
    const _parts = [(_emoji ? _emoji + " " : "") + _short];
    if (_provider) _parts.push("@" + _provider);
    if (_srcIdRaw) _parts.push("· " + _srcIdRaw);
    _alias = ruTitle + " (" + _parts.join(" ") + ")";
}
const _inheritTags = _isSource ? tpGetSourceTags(_src) : "";
const promptTags = await tp.system.prompt("Tags: ", _inheritTags);

await tp.file.rename(_fname);

function tpGetSourceTags(f) {
    const c = app.metadataCache.getFileCache(f) || {};
    const out = [];
    (c.tags || []).forEach(t => out.push(t.tag.replace(/^#/, "")));
    if (c.frontmatter && c.frontmatter.tags) [].concat(c.frontmatter.tags).forEach(t => out.push(String(t).replace(/^#/, "")));
    const exclude = new Set(["курс", "книга", "фокус"]);
    return [...new Set(out)].filter(t => t && !exclude.has(t)).map(t => "#" + t).join(" ");
}
-%>
---
type: learn-note
aliases: ["<% _alias %>"]
drafts: []
---
[Источник:: <% _srcLink %>] · <%* tR += promptTags %>

