// Two rows ticked, one open, for a look at the selection column.
await pw.fill('[data-slot="notes-tools"] input', 'sq020 050');
await wait(2500);
await pw.click('[data-slot="notes-row"]:nth-of-type(1) [data-slot="checkbox"]');
await pw.click('[data-slot="notes-row"]:nth-of-type(3) [data-slot="checkbox"]');
await pw.click('[data-slot="notes-row"]:nth-of-type(2) button');
await wait(1500);
return { verdict: $$('[data-slot="notes-row"][data-ticked]').length === 2 ? 'PASS' : 'FAIL', rows: $$('[data-slot="notes-row"]').length, count: text($('[data-slot="row-count"]')) };
