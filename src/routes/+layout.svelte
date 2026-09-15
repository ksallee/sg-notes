<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';

	import { apply, mode } from '$lib/theme';

	let { children } = $props();

	// `app.html` applied the look before the first paint; this keeps a `system` mode following the OS.
	$effect(() => {
		const media = matchMedia('(prefers-color-scheme: dark)');
		const follow = (): void => {
			if (mode() === 'system') apply();
		};
		media.addEventListener('change', follow);
		return () => media.removeEventListener('change', follow);
	});

</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>
{@render children()}
