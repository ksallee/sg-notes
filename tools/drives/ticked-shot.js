// A press selects a row alone; shift-press extends the run; option-press toggles one out; the
// pane stacks several with the last selected open; expand and collapse all work the stack.
await pw.fill('[data-slot="notes-tools"] input', 'sq020 050');
await wait(2500);
const row = (n) => `[data-slot="notes-row"]:nth-of-type(${n}) button[aria-pressed]`;
const selectedCount = () => $$('[data-slot="notes-row"][data-state="selected"]').length;
await pw.click(row(1));
await wait(300);
const one = { selected: selectedCount(), pane: Boolean($('[data-slot="thread-pane"]')) };
await pw.click(row(4), ['Shift']);
await wait(800);
const four = { selected: selectedCount(), stack: $$('[data-slot="thread-stack-item"]').map((el) => el.dataset.state) };
await pw.click(row(2), ['Alt']);
await wait(300);
const three = { selected: selectedCount(), label: text($('[data-slot="actions-button"]')) };
await pw.click('[data-slot="thread-stack"] [aria-label="Expand all"]');
await wait(300);
const allOpen = $$('[data-slot="thread-stack-item"][data-state="open"]').length;
await pw.click('[data-slot="thread-stack"] [aria-label="Collapse all"]');
await wait(300);
const noneOpen = $$('[data-slot="thread-stack-item"][data-state="open"]').length;
await pw.click('[data-slot="thread-stack-item"]:nth-of-type(1) button');
await wait(1200);
const ok = one.selected === 1 && one.pane && four.selected === 4 && four.stack.length === 4 && four.stack[3] === 'open' && four.stack.filter((s) => s === 'open').length === 1 && three.selected === 3 && allOpen === 3 && noneOpen === 0;
return { verdict: ok ? 'PASS' : 'FAIL see fields', one, four, three, allOpen, noneOpen };
