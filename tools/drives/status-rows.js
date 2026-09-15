// The status picker in the pane lists its options as a glyph and a name, as the filter bar's facet does.
await pw.click('[data-slot="notes-row"]:nth-of-type(1) button[aria-pressed]');
await wait(1200);
await pw.click('[data-slot="thread-pane"] [data-slot="picker-control"] button[aria-label*="statuses"], [data-slot="thread-pane"] button[aria-label="Show the statuses"]');
await wait(500);
const rows = $$('[role="option"], [data-slot="picker-row"]');
// An option is a glyph mark and plain text, never a badge (sg-widgets #228).
const glyphs = rows.filter((row) => row.querySelector('[data-slot="status-glyph"]')).length;
const badges = rows.filter((row) => row.querySelector('[data-slot="status-badge"]')).length;
return { verdict: rows.length > 0 && glyphs === rows.length && badges === 0 ? 'PASS' : 'FAIL see fields', rows: rows.length, glyphs, badges };
