// A shift-click on a row ticks the run from the open note; the pane stacks the ticked notes
// with the last one open.
await pw.fill('[data-slot="notes-tools"] input', 'sq020 050');
await wait(2500);
const row = (n) => `[data-slot="notes-row"]:nth-of-type(${n}) button[aria-pressed]`;
await pw.click(row(1));
await wait(300);
await pw.click(row(4), ['Shift']);
await wait(800);
const ticked = $$('[data-slot="notes-row"][data-ticked]').length;
const stack = $$('[data-slot="thread-stack-item"]').map((el) => el.dataset.state);
await pw.click(row(2), ['Alt']);
await wait(300);
const afterAlt = $$('[data-slot="notes-row"][data-ticked]').length;
await wait(1200);
return {
	verdict: ticked === 4 && stack.length === 4 && stack.filter((s) => s === 'open').length === 1 && stack[3] === 'open' && afterAlt === 3 ? 'PASS' : 'FAIL see fields',
	ticked,
	stack,
	afterAlt,
	count: text($('[data-slot="row-count"]')),
};
