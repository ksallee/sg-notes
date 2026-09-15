// Grouped by Task, a header names the task, its status, and the record it belongs to.
await pw.click('[data-slot="notes-tools"] [aria-label="Group by"]');
await wait(300);
await pw.click('[role="option"]:has-text("Task")');
await wait(800);
const headers = $$('[data-slot="notes-group"] > div').map(text);
const withOn = headers.filter((h) => / on /.test(h)).length;
return {
	verdict: withOn > 0 ? 'PASS' : 'FAIL no task header names its record',
	groups: headers.length,
	withOn,
	sample: headers.slice(0, 4),
	rowLinks: $$('[data-slot="notes-row-links"]').length,
};
