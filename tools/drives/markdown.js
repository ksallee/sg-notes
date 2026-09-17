// The search finds each probe by a phrase of its own. Each body renders once, however many were
// parsed before it: a shared lexer once handed every earlier body back with the next. A note's body renders as the site's markdown, and renders it safely: a raw tag shows as the
// characters typed, a javascript: link is text, an https link opens in a new tab.
const open = async (subject) => {
	await pw.fill('[data-slot="search"]', subject);
	await wait(2500);
	const row = $$('[data-slot="notes-row"]')[0];
	if (!row) return null;
	await pw.click(`[data-note-id="${row.dataset.noteId}"] button[aria-pressed]`);
	await wait(1200);
	return $('[data-slot="thread-pane"] [data-slot="markdown"]');
};
await wait(2000);
const html = await open('turnover sheet, tags and all');
const rawTag = html ? { b: html.querySelectorAll('b').length, text: /<b>not bold<\/b>/.test(html.textContent), once: (html.textContent.match(/Topology at the elbow/g) ?? []).length === 1 } : null;
const js = await open('pasting it as it came');
const jsLink = js ? { anchors: [...js.querySelectorAll('a')].map((a) => a.getAttribute('href')), text: /open the playlist/.test(js.textContent) } : null;
const table = await open('wire removal');
const tbl = table ? { tables: table.querySelectorAll('table').length, rows: table.querySelectorAll('tbody tr').length } : null;
const bold = await open('Needed for Thursday');
const strong = bold ? bold.querySelectorAll('strong').length : null;
const link = await open('wiki.example-studio.com');
const anchors = link ? [...link.querySelectorAll('a')].map((a) => ({ href: a.getAttribute('href'), target: a.target, rel: a.rel })) : null;
const pane = $('[data-slot="thread"]').getBoundingClientRect();
const ok = rawTag && rawTag.b === 0 && rawTag.text && rawTag.once && jsLink && jsLink.anchors.every((h) => !/^javascript/i.test(h ?? '')) && jsLink.text && tbl && tbl.tables === 1 && tbl.rows >= 2 && strong >= 1;
return { verdict: ok ? 'PASS' : 'FAIL see fields', rawTag, jsLink, tbl, strong, anchors, pane: [pane.left, pane.top].map(Math.round) };
