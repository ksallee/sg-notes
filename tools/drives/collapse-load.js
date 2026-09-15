// Collapse all, then the next page arrives: its groups arrive shut too, and one pressed open stays open.
await pw.click('[data-slot="notes-tools"] [aria-label="Collapse all"]');
await wait(300);
const groupsBefore = $$('[data-slot="notes-group"]').length;
await pw.click('[data-slot="notes-group"]:nth-of-type(2) [aria-expanded]');
await wait(200);
const scroller = $('[data-slot="notes-scroll"]');
scroller.scrollTop = scroller.scrollHeight;
await wait(3500);
const groupsAfter = $$('[data-slot="notes-group"]').length;
const open = $$('[data-slot="notes-group"] [aria-expanded="true"]').length;
const ok = groupsAfter > groupsBefore && open === 1;
return { verdict: ok ? 'PASS' : 'FAIL see fields', groupsBefore, groupsAfter, open };
