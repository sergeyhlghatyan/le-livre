<script lang="ts">
	import { parseReferences } from '$lib/utils/reference-parser';
	import CrossReferenceLink from './CrossReferenceLink.svelte';

	interface Props {
		text: string;
		currentSection?: string;
		currentYear?: number;
		currentProvisionHeading?: string;
		class?: string;
	}

	let {
		text,
		currentSection,
		currentYear = 2024,
		currentProvisionHeading = '',
		class: className = ''
	}: Props = $props();

	// Parse text into segments
	const segments = $derived(parseReferences(text, currentSection));
</script>

<div class={className}>
	{#each segments as segment}
		{#if segment.type === 'text'}
			{segment.content}
		{:else if segment.type === 'reference' && segment.reference}
			<CrossReferenceLink
				reference={segment.reference}
				{currentYear}
				{currentProvisionHeading}
			/>
		{/if}
	{/each}
</div>
