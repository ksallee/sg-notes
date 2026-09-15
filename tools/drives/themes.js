// The appearance menu changes the theme and the scheme, and the page follows at once.
const root = document.documentElement;
const bg = () => getComputedStyle(document.body).backgroundColor;
const start = { theme: root.dataset.sgTheme, dark: root.classList.contains('dark'), bg: bg() };
await pw.click('[data-slot="appearance"]');
await wait(300);
await pw.click('[role="menuitemradio"]:has-text("Supabase")');
await wait(300);
const supabase = { theme: root.dataset.sgTheme, bg: bg(), font: getComputedStyle(document.body).fontFamily.split(',')[0] };
await pw.click('[data-slot="appearance"]');
await wait(300);
await pw.click('[role="menuitemradio"]:has-text("Light")');
await wait(300);
const light = { dark: root.classList.contains('dark'), bg: bg(), scheme: root.style.colorScheme, stored: localStorage.getItem('sg-notes:mode') };
const ok = start.theme === 'weave' && start.dark && supabase.theme === 'supabase' && supabase.bg !== start.bg && /Outfit/.test(supabase.font) && !light.dark && light.bg !== supabase.bg && light.stored === 'light';
return { verdict: ok ? 'PASS' : 'FAIL see fields', start, supabase, light };
