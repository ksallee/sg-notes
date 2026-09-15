// Tick two notes, close them through the palette, then reply to both.
const rowSel = '[data-slot="notes-row"]';
const statusOf = (li) => li.querySelector('[data-slot="status-badge"]')?.getAttribute('title') || text(li.querySelector('[data-slot="status-badge"]'));
const first = $$(rowSel).slice(0, 2);
if (first.length < 2) return { verdict: 'FAIL fewer than two rows' };
const keys = first.map((li) => li.dataset.rowKey);
await pw.click(`${rowSel}:nth-of-type(1) [data-slot="checkbox"]`);
await pw.click(`${rowSel}:nth-of-type(2) [data-slot="checkbox"]`);
await wait(200);
const tickedLabel = text($('[data-slot="actions-button"]'));

await pw.press('body', 'Meta+k');
await wait(400);
if (!$('[data-slot="command-item"]')) return { verdict: 'FAIL the palette did not open', tickedLabel };
await pw.click('[data-slot="command-item"]:has-text("Set the status")');
await wait(300);
await pw.click('[data-slot="command-item"]:has-text("Closed")');
await wait(4000);
const jobText = text($('[data-slot="job-dialog"]'));
await pw.click('[data-slot="job-dialog"] button:has-text("Done")');
await wait(1500);
const after = keys.map((key) => statusOf($(`[data-row-key="${key}"]`)));

await pw.press('body', 'Meta+k');
await wait(400);
await pw.click('[data-slot="command-item"]:has-text("Reply to")');
await wait(400);
await pw.fill('[data-slot="reply-dialog"] textarea', `bulk qa reply ${new Date().toISOString()}`);
await pw.click('[data-slot="reply-dialog"] button[type="submit"]');
await wait(5000);
const replyJob = text($('[data-slot="job-dialog"]'));
await pw.click('[data-slot="job-dialog"] button:has-text("Done")');
await wait(1500);
const counts = keys.map((key) => text($(`[data-row-key="${key}"] [title$="replies"]`)));

const ok = /All 2 done/.test(jobText) && after.every((s) => /Closed|clsd/.test(s)) && /All 2 done/.test(replyJob);
return { verdict: ok ? 'PASS' : 'FAIL see fields', tickedLabel, jobText, after, replyJob, counts };
