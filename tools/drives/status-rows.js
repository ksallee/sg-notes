// The status picker in the pane lists its options as badges, as the filter bar's facet does.
await pw.click('[data-slot="notes-row"]:nth-of-type(1) button[aria-pressed]');
await wait(1200);
await pw.click('[data-slot="thread-pane"] [data-slot="picker-control"] button[aria-label*="statuses"], [data-slot="thread-pane"] button[aria-label="Show the statuses"]');
await wait(500);
const rows = $$('[role="option"], [data-slot="picker-row"]');
const badges = rows.filter((row) => row.querySelector('[data-slot="status-badge"]')).length;
await pw.press('body', 'Escape');
return { verdict: rows.length > 0 && badges === rows.length ? 'PASS' : 'FAIL see fields', rows: rows.length, badges };
