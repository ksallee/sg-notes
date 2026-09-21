// The view the README shows: the project's notes under their records, one thread open.
//
// The set is narrowed to the two seeded artist accounts and to the notes whose author
// owes the next word, so nothing in frame names the person whose site this is, and the
// site's host is replaced by the studio name the sign-in field offers as its example.
// The verdict fails if any of the three reaches the viewport.
const pick = async (pill, values) => {
	await pw.click(`button:has-text("${pill}")`);
	await wait(800);
	for (const value of values) {
		await pw.click(`[data-slot="command-item"][data-value="${value}"]`);
		await wait(400);
	}
	await pw.press('body', 'Escape');
	await wait(600);
};

// From: Other Artist, then Kevin Artist.
await pick('From', ['HumanUser:517', 'HumanUser:451']);
await pw.click('[data-slot="notes-tools"] [aria-label="Waiting on"]');
await wait(400);
await pw.click('[role="option"]:has-text("The author")');
await wait(1200);

const host = $('[data-slot="site-bar"] span[title^="http"]');
if (!host) return { verdict: 'FAIL the site label moved' };
host.removeAttribute('title');
host.lastChild.nodeValue = ' studio';

const rows = $$('[data-slot="notes-row"]');
if (rows.length < 6) return { verdict: `FAIL only ${rows.length} rows`, count: text($('[data-slot="row-count"]')) };
// The note the thread shows: an exchange between the two artists, chosen by subject so the
// shot is the same one every run.
const open = rows.find((row) => /jitter/.test(row.textContent));
if (!open) return { verdict: 'FAIL the jitter note is not in the set' };
open.querySelector('button[aria-pressed]').click();
// The thread's replies land after the pane does, and the shot is taken once this returns:
// the page has to be still before what is in frame can be read.
await wait(4000);

const seen = new Set();
for (const el of $$('body *')) {
	const box = el.getBoundingClientRect();
	if (box.bottom <= 0 || box.top >= innerHeight || box.right <= 0 || box.left >= innerWidth) continue;
	for (const node of el.childNodes) if (node.nodeType === 3 && node.textContent.trim()) seen.add(node.textContent.trim());
}
const inFrame = [...seen].join(' ');
const named = ['Sallee', 'kevinsallee', 'comfyui-fpt'].filter((word) => inFrame.includes(word));

const pane = $('[data-slot="thread-pane"]');
return {
	verdict: named.length > 0 ? `FAIL in frame: ${named.join(', ')}` : pane ? 'PASS' : 'FAIL the thread did not open',
	count: text($('[data-slot="row-count"]')),
	groups: $$('[data-slot="notes-group"]').length,
	rows: $$('[data-slot="notes-row"]').length,
	thread: text($('h2', pane)),
	waiting: text($('[data-slot="thread-waiting"]', pane))
};
