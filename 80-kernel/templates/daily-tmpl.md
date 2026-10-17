<%*
const m = moment().locale("en");
const day = m.format("DD");
const monthLower = m.format("MMMM").toLowerCase();
const year = m.format("YYYY");
const ym = year + "/" + m.format("MM") + "-" + monthLower;
// D-001 — первый день дневника; поставьте дату своего первого дня (DD-MM-YYYY).
const EPOCH = "01-01-2027";
const counter = m.diff(moment(EPOCH, "DD-MM-YYYY"), "days") + 1;
const cnt = String(counter).padStart(3, "0");
const fileName = `D-${cnt}-${day}-${monthLower}-${year}`;
await tp.file.move(`20-library/journal/${ym}/${fileName}`);
-%>
---
type: journal
created: <% tp.date.now("YYYY-MM-DD HH:mm") %>
cssclasses:
- hide-properties
---
# <% tp.date.now("dddd, D MMMM YYYY") %>
---
<% tp.file.cursor(1) %>
