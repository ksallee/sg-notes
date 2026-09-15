// Arrows move the selection, shift-arrows extend it, ⌘A takes every loaded row.
const row = (n) => `[data-slot="notes-row"]:nth-of-type(${n}) button[aria-pressed]`;
const selectedIds = () => $$('[data-slot="notes-row"][data-state="selected"]').map((el) => el.dataset.noteId);
await pw.click(row(1));
await wait(200);
const first = selectedIds();
await pw.press(row(1), 'ArrowDown');
await wait(200);
const moved = selectedIds();
await pw.press(row(2), 'Shift+ArrowDown');
await wait(200);
const extended = selectedIds();
await pw.press(row(3), 'Meta+a');
await wait(300);
const all = selectedIds().length;
const rows = $$('[data-slot="notes-row"]').length;
const ok = first.length === 1 && moved.length === 1 && moved[0] !== first[0] && extended.length === 2 && all === rows;
return { verdict: ok ? 'PASS' : 'FAIL see fields', first, moved, extended, all, rows };
