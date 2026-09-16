#!/usr/bin/env node
// Drive the app headless and print only what the drive returns.
//
//   node tools/qa.mjs --project 1180 --drive tools/drives/lead-view.js
//   node tools/qa.mjs --project 1180 --shot .playwright-mcp/lead.png --theme paper --mode light
//
// Starts `vite dev` on a free port unless --url names a running server, so the dev-only
// /live/dev-token endpoint signs the page in from .env.local and nobody has to approve a
// request. --project writes the project pick the page reads from localStorage. The drive
// is the body of an async function receiving ({wait, $, $$, text, pw}); `pw.click`, `pw.fill`
// and `pw.press` take a Playwright selector and act with real input events, for controls that
// ignore synthetic ones (a Bits UI select opens on a pointer sequence); `pw.click(sel, ['Shift'])`
// holds modifiers. The return value is
// printed as `result`, and the exit code is 1 when the page threw, the console logged an
// error, or `result.verdict` starts with FAIL. Console errors and warnings are printed;
// nothing else is, so a run costs a few lines.
import { spawn } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { createServer } from 'node:net';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');

function args(argv) {
	const a = { path: '/', viewport: '1440x900', timeout: 30000, settle: 5000 };
	for (let i = 0; i < argv.length; i++) {
		const k = argv[i];
		const next = () => argv[++i];
		switch (k) {
			case '--url': a.url = next(); break;
			case '--path': a.path = next(); break;
			case '--drive': a.drive = next(); break;
			case '--shot': a.shot = next(); break;
			case '--viewport': a.viewport = next(); break;
			case '--timeout': a.timeout = Number(next()); break;
			case '--settle': a.settle = Number(next()); break;
			case '--project': a.project = Number(next()); break;
			case '--theme': a.theme = next(); break;
			case '--log-requests': a.logRequests = new RegExp(next()); break;
			case '--mode': a.mode = next(); break;
			case '--reduced-motion': a.reducedMotion = true; break;
			case '--headed': a.headed = true; break;
			default: throw new Error(`unknown flag ${k}`);
		}
	}
	return a;
}

function freePort(start = 5190) {
	return new Promise((res) => {
		const s = createServer();
		s.once('error', () => res(freePort(start + 1)));
		s.listen(start, '127.0.0.1', () => s.close(() => res(start)));
	});
}

async function startDev(port) {
	const proc = spawn('./node_modules/.bin/vite', ['dev', '--host', '127.0.0.1', '--port', String(port), '--strictPort'], {
		cwd: ROOT,
		stdio: ['ignore', 'pipe', 'pipe'],
	});
	// An unread pipe fills at 64KB and blocks the writer.
	proc.stdout.resume();
	proc.stderr.resume();
	const deadline = Date.now() + 60000;
	while (Date.now() < deadline) {
		try {
			if ((await fetch(`http://127.0.0.1:${port}/`)).ok) return proc;
		} catch {}
		if (proc.exitCode !== null) throw new Error(`vite dev exited ${proc.exitCode}`);
		await new Promise((r) => setTimeout(r, 250));
	}
	proc.kill();
	throw new Error('vite dev did not become ready in 60s');
}

function boot(ctx) {
	const wait = (ms) => new Promise((r) => setTimeout(r, ms));
	const $ = (s, root = document) => root.querySelector(s);
	const $$ = (s, root = document) => [...root.querySelectorAll(s)];
	const text = (el) => (el ? el.textContent.replace(/\s+/g, ' ').trim() : '');
	const pw = {
		click: (selector, modifiers) => window.__pw('click', selector, modifiers),
		fill: (selector, value) => window.__pw('fill', selector, value),
		press: (selector, key) => window.__pw('press', selector, key),
	};
	const fn = new Function('ctx', 'return (async () => { const {wait, $, $$, text, pw} = ctx; ' + ctx.drive + ' })()');
	return fn({ wait, $, $$, text, pw });
}

async function main() {
	const a = args(process.argv.slice(2));
	const [vw, vh] = a.viewport.split('x').map(Number);
	let proc = null;
	let url = a.url;
	if (!url) {
		const port = await freePort();
		proc = await startDev(port);
		url = `http://127.0.0.1:${port}`;
	}
	url = url.replace(/\/$/, '') + a.path;
	const drive = a.drive ? readFileSync(a.drive, 'utf8') : 'return {};';

	const browser = await chromium.launch({ headless: !a.headed });
	const ctx = await browser.newContext({
		viewport: { width: vw, height: vh },
		reducedMotion: a.reducedMotion ? 'reduce' : 'no-preference',
	});
	if (a.project) {
		await ctx.addInitScript((id) => localStorage.setItem('sg-notes:project', JSON.stringify({ id })), a.project);
	}
	// The look, from the keys $lib/theme reads: `--theme default|supabase|claude`, `--mode light|dark|system`.
	if (a.theme || a.mode) {
		await ctx.addInitScript(
			([theme, mode]) => {
				if (theme) localStorage.setItem('sg-notes:theme', theme);
				if (mode) localStorage.setItem('sg-notes:mode', mode);
			},
			[a.theme ?? '', a.mode ?? '']
		);
	}
	const page = await ctx.newPage();
	const console_ = [];
	page.on('console', (m) => {
		if (m.type() === 'error' || m.type() === 'warning') console_.push(`${m.type()}: ${m.text()}`);
	});
	page.on('pageerror', (e) => console_.push(`pageerror: ${e.message}`));
	// `--log-requests <regex>`: the method, url and body of every matching request, printed under `requests`.
	const requests = [];
	if (a.logRequests) {
		page.on('request', (req) => {
			if (a.logRequests.test(req.url())) requests.push({ method: req.method(), url: req.url().replace(/^https?:\/\/[^/]+/, ''), body: req.postData() ?? null });
		});
	}
	// A navigation mid-drive is worth knowing about: Vite's own console line says why when it is Vite.
	page.on('framenavigated', (frame) => {
		if (frame === page.mainFrame()) console_.push(`navigated: ${frame.url()}`);
	});
	page.on('console', (m) => {
		if (m.text().includes('[vite]')) console_.push(`vite: ${m.text()}`);
	});
	await page.exposeFunction('__pw', async (action, selector, value) => {
		const el = page.locator(selector).first();
		if (action === 'click') await el.click({ timeout: 5000, ...(Array.isArray(value) ? { modifiers: value } : {}) });
		else if (action === 'fill') await el.fill(value, { timeout: 5000 });
		else if (action === 'press') await el.press(value, { timeout: 5000 });
		return true;
	});

	let result = null;
	let failed = false;
	try {
		await page.goto(url, { waitUntil: 'load', timeout: a.timeout });
		// A dev server just started re-optimises dependencies as the page discovers them and
		// reloads it, which would tear the drive down mid-run: let it, then load again.
		if (proc) {
			await page.waitForTimeout(2000);
			await page.goto(url, { waitUntil: 'load', timeout: a.timeout });
		}
		// The page reads the site after it loads; give the first reads time to land.
		await page.waitForTimeout(a.settle);
		try {
			result = await page.evaluate(boot, { drive });
		} catch (error) {
			// One late reload is forgiven: the page is back, so the drive runs once more.
			if (!String(error).includes('Execution context was destroyed')) throw error;
			await page.waitForTimeout(a.settle);
			result = await page.evaluate(boot, { drive });
		}
		if (a.shot) await page.screenshot({ path: resolve(a.shot) });
	} catch (error) {
		failed = true;
		result = { error: error instanceof Error ? error.message : String(error) };
	}
	await browser.close();
	proc?.kill();

	const errors = console_.filter((line) => !line.includes('favicon.ico'));
	const out = { result, ...(errors.length ? { console: errors } : {}), ...(a.logRequests ? { requests } : {}), ...(a.shot ? { shot: a.shot } : {}) };
	console.log(JSON.stringify(out, null, 1));
	const verdict = result && typeof result.verdict === 'string' ? result.verdict : '';
	process.exit(failed || errors.some((l) => l.startsWith('error') || l.startsWith('pageerror')) || verdict.startsWith('FAIL') ? 1 : 0);
}

main().catch((error) => {
	console.error(error);
	process.exit(1);
});
