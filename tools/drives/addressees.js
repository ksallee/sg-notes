// Three notes selected: the dialog shows the people on all of them as chips, the rest as
// "on n of 3" with a plus and a cross, and Save stays off until something changes.
await pw.fill('[data-slot="notes-tools"] input', 'sq020 050');
await wait(2500);
const row = (n) => `[data-slot="notes-row"]:nth-of-type(${n}) button[aria-pressed]`;
await pw.click(row(1));
await pw.click(row(3), ['Shift']);
await wait(400);
await pw.press(row(3), 'f');
await wait(600);
const dialog = $('[data-slot="address-dialog"]');
if (!dialog) return { verdict: 'FAIL the dialog did not open' };
const lines = $$('[data-slot="address-line"]', dialog).map((line) => ({
	field: line.dataset.field,
	chips: $$('[data-slot="entity-chip"], [data-slot="picker-chip"]', line).length,
	partial: $$('li', line).map(text),
}));
const saveOff = $('button[type="submit"]', dialog).disabled;
const plus = $('[data-slot="address-line"][data-field="addressings_to"] li button[aria-label^="Put"]', dialog);
if (plus) plus.click();
await wait(200);
const saveOn = !$('button[type="submit"]', dialog).disabled;
await pw.press('body', 'Escape');
await wait(300);
const ok = lines.length === 2 && saveOff && (!plus || saveOn) && Boolean($('[data-slot="address-dialog"]')) === false;
return { verdict: ok ? 'PASS' : 'FAIL see fields', lines, saveOff, saveOn };
