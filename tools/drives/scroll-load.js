// Scrolling to the foot of the list reads the next page without a press.
const rows = () => $$('[data-slot="notes-row"]').length;
const before = rows();
const scroller = $('[data-slot="notes-scroll"]');
scroller.scrollTop = scroller.scrollHeight;
await wait(3500);
const after = rows();
return { verdict: after > before ? 'PASS' : 'FAIL see fields', before, after, count: text($('[data-slot="row-count"]')) };
