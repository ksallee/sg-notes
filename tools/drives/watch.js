// The page notices what someone else did without a reload. A reply written straight to the site
// reaches the row's thread count in place, with the list never dimmed; a note written to the
// project shows as a pill, and the pill brings it in. The writes go through the dev token, as the
// script, so this needs the script's ApiUser to generate event log entries (finding 049).
await wait(2000);
const token = await (await fetch('/live/dev-token', { method: 'POST' })).json();
if (!token.accessToken) return { verdict: 'FAIL no dev token: this drive writes through the script key' };
const api = async (path, body) => {
	const res = await fetch(`${token.siteUrl}/api/v1${path}`, { method: 'POST', headers: { Authorization: `Bearer ${token.accessToken}`, 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify(body) });
	return { status: res.status, body: await res.json().catch(() => null) };
};
const stamp = new Date().toISOString();
const row = $$('[data-slot="notes-row"]').find((r) => r.dataset.unread !== 'x');
const noteId = Number(row.dataset.noteId);
const replyCount = (r) => { const badge = r?.querySelector('[title$=" replies"]'); return badge ? Number(badge.title.split(' ')[0]) : 0; };
const before = replyCount(row);

// 1. A reply from elsewhere.
const reply = await api('/entity/replies', { content: `watch qa reply ${stamp}`, entity: { type: 'Note', id: noteId } });
if (reply.status !== 201) return { verdict: 'FAIL the reply write failed', reply };
let dimmed = false; let after = before; let waited = 0;
while (waited < 45000) {
	await wait(500); waited += 500;
	if ($('[data-slot="notes-scroll"]')?.getAttribute('aria-busy') === 'true') dimmed = true;
	after = replyCount($(`[data-note-id="${noteId}"]`));
	if (after > before) break;
}
const replySeen = after > before;

// 2. A note from elsewhere: the pill, then the note itself once shown.
const note = await api('/entity/notes', { project: { type: 'Project', id: Number(localStorage.getItem('sg-notes:project') && JSON.parse(localStorage.getItem('sg-notes:project')).id) }, subject: `watch qa note ${stamp}`, content: `Written beside the page at ${stamp}.` });
if (note.status !== 201) return { verdict: 'FAIL the note write failed', note, replySeen, waited };
let pill = null; waited = 0;
while (waited < 45000 && !pill) { await wait(500); waited += 500; pill = $('[data-slot="new-notes"]'); }
const pillText = pill ? text(pill) : null;
let shown = false;
if (pill) {
	await pw.click('[data-slot="new-notes"]');
	await wait(4000);
	shown = !!$(`[data-note-id="${note.body.data.id}"]`);
}
const ok = replySeen && !dimmed && /1 new note/.test(pillText ?? '') && shown && !$('[data-slot="new-notes"]');
return { verdict: ok ? 'PASS' : 'FAIL see fields', noteId, before, after, dimmed, replySeen, pillText, shown, newNote: note.body?.data?.id };
