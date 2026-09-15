// Search narrows the set on the site, the group-by switch regroups the same rows, and
// collapse all shuts every group.
const count = () => text($('[data-slot="row-count"]'));
const rows = () => $$('[data-slot="notes-row"]').length;
const groups = () => $$('[data-slot="notes-group"]').length;
const headers = () => $$('[data-slot="notes-group"] > div').map(text);
const before = { count: count(), rows: rows(), groups: groups() };

await pw.fill('[data-slot="notes-tools"] input', 'sh040');
await wait(2500);
const searched = { count: count(), rows: rows(), groups: groups(), headers: headers() };
await pw.fill('[data-slot="notes-tools"] input', 'other artist');
await wait(2500);
const byPerson = { count: count(), rows: rows() };
await pw.fill('[data-slot="notes-tools"] input', 'closed');
await wait(2500);
const byStatusWord = { count: count(), rows: rows() };
await pw.fill('[data-slot="notes-tools"] input', '');
await wait(2500);

await pw.click('[data-slot="notes-tools"] [aria-label="Group by"]');
await wait(300);
await pw.click('[role="option"]:has-text("Status")');
await wait(500);
const byStatus = { groupBy: $('[data-slot="notes-list"]').dataset.groupBy, groups: groups(), headers: headers() };

await pw.click('[data-slot="notes-tools"] [aria-label="Collapse all"]');
await wait(300);
const collapsed = { rows: rows(), expanded: $$('[data-slot="notes-group"] [aria-expanded="true"]').length };

// Back to Record: its groups are still open, and back to Status they are still shut.
await pw.click('[data-slot="notes-tools"] [aria-label="Group by"]');
await wait(300);
await pw.click('[role="option"]:has-text("Record")');
await wait(300);
const backOnRecord = { groupBy: $('[data-slot="notes-list"]').dataset.groupBy, rows: rows() };
await pw.click('[data-slot="notes-tools"] [aria-label="Group by"]');
await wait(300);
await pw.click('[role="option"]:has-text("Status")');
await wait(300);
const backOnStatus = { rows: rows() };
await pw.click('[data-slot="notes-tools"] [aria-label="Expand all"]');
await wait(300);

const ok =
	searched.rows < before.rows && searched.rows > 0 && byPerson.rows > 0 && byStatusWord.rows > 0 &&
	byStatus.groupBy === 'status' && byStatus.groups < before.groups &&
	// Collapsing every group brings the foot into view, which reads the rest of the set in.
	collapsed.rows === 0 && backOnRecord.rows >= before.rows && backOnStatus.rows === 0 && rows() >= before.rows;
return { verdict: ok ? 'PASS' : 'FAIL see fields', before, searched, byPerson, byStatusWord, byStatus, collapsed, backOnRecord, backOnStatus, restored: rows() };
