/**
 * What the page wears: a theme, and light or dark.
 *
 * Three themes, each a full set of the shadcn tokens in both schemes, in
 * `app.css`, all three the sg-widgets docs site's own: Default, the one it wears
 * by default and the default here; Supabase and Claude, two of the presets it
 * offers, with the corrections it made where a preset missed AA. The page is a
 * place to see the widgets wear a palette they were not drawn on, and to see
 * them sit beside primitives that are not sg-widgets' own.
 *
 * The theme lands as `data-sg-theme` on `<html>` and the scheme as the `.dark`
 * class, which is what the token sheet keys on. `app.html` applies both before
 * the first paint from the same storage keys, so there is no flash.
 */
export type Theme = 'default' | 'supabase' | 'claude';
export type Mode = 'light' | 'dark' | 'system';

export const THEMES: ReadonlyArray<{ value: Theme; label: string; note: string }> = [
	{ value: 'default', label: 'Default', note: 'The sg-widgets default, in Geist' },
	{ value: 'supabase', label: 'Supabase', note: 'Neutral with a green accent, in Outfit' },
	{ value: 'claude', label: 'Claude', note: 'Warm ink and orange, in the system face' }
];

export const MODES: ReadonlyArray<{ value: Mode; label: string }> = [
	{ value: 'light', label: 'Light' },
	{ value: 'dark', label: 'Dark' },
	{ value: 'system', label: 'System' }
];

export const KEYS = { theme: 'sg-notes:theme', mode: 'sg-notes:mode' } as const;

function read(key: string): string | null {
	try {
		return localStorage.getItem(key);
	} catch {
		return null;
	}
}

function write(key: string, value: string): void {
	try {
		localStorage.setItem(key, value);
	} catch {
		/* A remembered look is a convenience. */
	}
}

export function theme(): Theme {
	const value = read(KEYS.theme);
	return THEMES.some((option) => option.value === value) ? (value as Theme) : 'default';
}

export function mode(): Mode {
	const value = read(KEYS.mode);
	return MODES.some((option) => option.value === value) ? (value as Mode) : 'dark';
}

/** Whether the page is dark now, given the mode and the system. */
export function isDark(current: Mode = mode()): boolean {
	return current === 'dark' || (current === 'system' && matchMedia('(prefers-color-scheme: dark)').matches);
}

/** Put the theme and the scheme on the document. The same rule as the inline script in `app.html`. */
export function apply(nextTheme: Theme = theme(), nextMode: Mode = mode()): void {
	const root = document.documentElement;
	root.dataset.sgTheme = nextTheme;
	root.classList.toggle('dark', isDark(nextMode));
	root.style.colorScheme = isDark(nextMode) ? 'dark' : 'light';
}

export function setTheme(next: Theme): void {
	write(KEYS.theme, next);
	apply(next, mode());
}

export function setMode(next: Mode): void {
	write(KEYS.mode, next);
	apply(theme(), next);
}
