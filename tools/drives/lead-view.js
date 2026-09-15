// The lead view on the sandbox: the bar reads the project, the list groups notes under
// records, a click opens the thread, and nothing overflows its box.
const bar = $('[data-slot="site-bar"]');
const groups = $$('[data-slot="notes-group"]');
const rows = $$('[data-slot="notes-row"]');
if (!bar) return { verdict: 'FAIL no site bar' };
if (rows.length === 0) return { verdict: 'FAIL no note rows', count: text($('[data-slot="row-count"]')) };
rows[0].querySelector('button').click();
await wait(1500);
const thread = $('[data-slot="thread-pane"]');
// Text cut off without a truncate rule: a box whose content is wider than it and is visible.
const overflowing = $$('[data-slot="notes-list"] *, [data-slot="thread-pane"] *').filter((el) => {
	if (el.scrollWidth <= el.clientWidth + 1 || el.closest('.truncate')) return false;
	const style = getComputedStyle(el);
	return style.overflowX === 'visible' && [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
}).length;
return {
	verdict: thread ? (overflowing === 0 ? 'PASS' : `FAIL ${overflowing} elements overflow`) : 'FAIL the thread did not open',
	count: text($('[data-slot="row-count"]')),
	groups: groups.length,
	rows: rows.length,
	unread: $$('[data-slot="notes-row"][data-unread]').length,
	facets: $$('[data-slot="workbench"] > div:first-child button').map((b) => text(b) + (b.disabled ? ' (disabled)' : '')),
	firstGroup: text(groups[0]?.firstElementChild),
	firstRow: text(rows[0]),
	thread: {
		title: text($('h2', thread)),
		replies: $$('[data-slot="thread-replies"] li', thread).length,
		waiting: text($('[data-slot="thread-waiting"]', thread)),
		reply: $('textarea', thread)?.disabled ? 'disabled' : 'enabled',
	},
};
