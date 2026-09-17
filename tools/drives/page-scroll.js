// Only the list and the pane scroll: the document never grows past the viewport in either
// direction, so the wheel at the bottom of the list has nowhere to hand over to and the pane
// stays on the page however long a row's preview line is.
await wait(1500);
const list = $('[data-slot="notes-scroll"]');
list.scrollTop = list.scrollHeight;
await wait(100);
window.scrollTo(0, 300);
await wait(50);
const page = { scrollY, htmlScroll: document.documentElement.scrollHeight, viewport: innerHeight, htmlWidth: document.documentElement.scrollWidth, viewportWidth: innerWidth, listScrolls: list.scrollHeight > list.clientHeight };
const ok = page.scrollY === 0 && page.htmlScroll === page.viewport && page.htmlWidth === page.viewportWidth && page.listScrolls;
return { verdict: ok ? 'PASS' : 'FAIL the page scrolls', ...page };
