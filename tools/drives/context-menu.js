// A right-click on a row selects it and opens the verbs on the selection; on a selected row it keeps
// the selection; Reply… opens the palette's reply dialog for that many notes.
const row = (n) => `[data-slot="notes-row"]:nth-of-type(${n}) button[aria-pressed]`;
const selectedIds = () => $$('[data-slot="notes-row"][data-state="selected"]').map((r) => r.dataset.noteId);
const menuItems = () => $$('[data-slot="notes-menu"] [role="menuitem"]').map((el) => el.textContent.trim().replace(/\s+/g, ' '));
await wait(1500);
await pw.rightClick(row(1));
await wait(400);
const one = { selected: selectedIds(), items: menuItems() };
await pw.press('body', 'Escape');
await wait(300);
await pw.rightClick(row(3));
await wait(400);
const three = { selected: selectedIds(), open: !!$('[data-slot="notes-menu"]') };
await pw.press('body', 'Escape');
await wait(300);
await pw.click(row(2), ['Shift']);
await wait(300);
await pw.rightClick(row(3));
await wait(400);
const run = { selected: selectedIds(), heading: text($('[data-slot="notes-menu"] [data-slot="context-menu-group-heading"]')) };
const menu = $('[data-slot="notes-menu"]');
if (!menu) return { verdict: 'FAIL no menu on a right-click inside the selection', one, three, run };
const menuBox = menu.getBoundingClientRect();
await pw.click('[data-slot="notes-menu"] [role="menuitem"]:has-text("Reply…")');
await wait(500);
const dialog = text($('[data-slot="reply-dialog"] h2, [data-slot="reply-dialog"] [data-slot="dialog-title"]'));
await pw.press('body', 'Escape');
await wait(300);
const ok =
	one.selected.length === 1 && one.items.some((t) => /^Reply…/.test(t)) && one.items.some((t) => /Sync from SG/.test(t)) && one.items.some((t) => /Set status/.test(t)) &&
	three.open && three.selected.length === 1 && three.selected[0] !== one.selected[0] &&
	run.selected.length === 2 && /2 notes/.test(run.heading) && /Reply to 2 notes/.test(dialog) && !$('[data-slot="reply-dialog"]');
return { verdict: ok ? 'PASS' : 'FAIL see fields', one, three, run, dialog, menuBox: [menuBox.left, menuBox.top, menuBox.right, menuBox.bottom].map(Math.round) };
