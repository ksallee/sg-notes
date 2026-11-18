// ⌘K → Search leaves focus in the search box, and a search runs without a 400 (issue #6).
await pw.click('[data-slot="notes-row"]:nth-of-type(1) button[aria-pressed]');
await wait(200);
await pw.press('body', 'Meta+k');
await wait(400);
const paletteOpen = !!$('[data-slot="palette"]');
await pw.fill('[data-slot="palette"] input', 'search');
await wait(200);
await pw.press('[data-slot="palette"] input', 'Enter');
await wait(600);
const focused = document.activeElement?.getAttribute('data-slot');
await pw.press('[data-slot="search"]', 's');
await pw.press('[data-slot="search"]', 'h');
await wait(2500);
const query = $('[data-slot="search"]')?.value;
const rows = $$('[data-slot="notes-row"]').length;
const ok = paletteOpen && focused === 'search' && query === 'sh';
return { verdict: ok ? 'PASS' : 'FAIL see fields', paletteOpen, focused, query, rows };
