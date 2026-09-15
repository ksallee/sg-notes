<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();

	// The token sheet keys dark mode on `.dark`; the page follows the system setting.
	$effect(() => {
		const media = matchMedia('(prefers-color-scheme: dark)');
		const follow = (): void => {
			document.documentElement.classList.toggle('dark', media.matches);
		};
		follow();
		media.addEventListener('change', follow);
		return () => media.removeEventListener('change', follow);
	});
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>
{@render children()}
