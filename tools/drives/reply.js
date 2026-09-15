// A reply written from the pane lands in the thread and in the row's count.
const rows = $$('[data-slot="notes-row"]');
if (rows.length === 0) return { verdict: 'FAIL no note rows' };
rows[0].querySelector('button[aria-pressed]').click();
await wait(1500);
const pane = $('[data-slot="thread-pane"]');
const before = $$('[data-thread-type="Reply"]', pane).length;
const box = $('textarea', pane);
if (!box || box.disabled) return { verdict: 'FAIL the reply box is disabled' };
const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
setter.call(box, `qa reply ${new Date().toISOString()}`);
box.dispatchEvent(new Event('input', { bubbles: true }));
await wait(50);
$('form button[type="submit"]', pane).click();
await wait(4000);
const after = $$('[data-thread-type="Reply"]', pane).length;
const failure = text($('form .text-destructive', pane));
return {
	verdict: after === before + 1 ? 'PASS' : `FAIL replies ${before} -> ${after} ${failure}`,
	rowCount: text(rows[0].querySelector('[title$="replies"]')),
	waiting: text($('[data-slot="thread-waiting"]', pane)),
};
