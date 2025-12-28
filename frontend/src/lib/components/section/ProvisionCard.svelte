<script lang="ts">
	import ProvisionTypeBadge from './ProvisionTypeBadge.svelte';
	import TextLengthIndicator from './TextLengthIndicator.svelte';
	import ChildCountIndicator from './ChildCountIndicator.svelte';
	import RevisionHistoryBadge from './RevisionHistoryBadge.svelte';
	import ReferenceCountIndicator from './ReferenceCountIndicator.svelte';
	import ActionButtons from './ActionButtons.svelte';

	interface Provision {
		provision_id: string;
		provision_level: string;
		provision_num: string;
		text_content: string;
		heading?: string | null;
	}

	interface Props {
		provision: Provision;
		selectedYear: number;
		childCount: number;
		revisionCount: number;
		referenceCount: number;
		indentLevel: number;
	}

	let { provision, selectedYear, childCount, revisionCount, referenceCount, indentLevel }: Props = $props();

	function truncateText(text: string | undefined | null, maxLength: number): string {
		if (!text) return '';
		if (text.length <= maxLength) return text;
		return text.substring(0, maxLength) + '...';
	}

	function getBorderColor(level: string): string {
		const colorMap: Record<string, string> = {
			section: 'border-l-blue-500',
			subsection: 'border-l-purple-500',
			paragraph: 'border-l-green-500',
			clause: 'border-l-amber-500',
			subclause: 'border-l-pink-500',
			item: 'border-l-gray-500'
		};

		return colorMap[level.toLowerCase()] || colorMap.item;
	}

	function getBorderWidth(level: string): string {
		const widthMap: Record<string, string> = {
			section: 'border-l-4',
			subsection: 'border-l-[3px]',
			paragraph: 'border-l-2',
			clause: 'border-l',
			subclause: 'border-l',
			item: 'border-l'
		};

		return widthMap[level.toLowerCase()] || widthMap.item;
	}
</script>

<div class="provision-card" style="margin-left: {indentLevel * 2}rem">
	<div
		class="card-content {getBorderWidth(provision.provision_level)} {getBorderColor(provision.provision_level)}"
	>
		<!-- Header row -->
		<div class="header-row">
			<ProvisionTypeBadge level={provision.provision_level} />
			<h3 class="provision-heading">
				{provision.provision_num}
				{#if provision.heading}
					<span class="heading-text">{provision.heading}</span>
				{/if}
			</h3>
			<div class="badges-right">
				<RevisionHistoryBadge count={revisionCount} />
			</div>
		</div>

		<!-- Text preview -->
		<div class="text-preview">
			<p>{truncateText(provision.text_content, 250)}</p>
			{#if provision.text_content && provision.text_content.length > 250}
				<span class="fade-overlay"></span>
			{/if}
		</div>

		<!-- Metadata row -->
		<div class="metadata-row">
			<TextLengthIndicator length={provision.text_content?.length || 0} />
			<ChildCountIndicator count={childCount} />
			<ReferenceCountIndicator count={referenceCount} />
			<ActionButtons provisionId={provision.provision_id} year={selectedYear} />
		</div>
	</div>
</div>

<style>
	.provision-card {
		@apply transition-all duration-200;
	}

	.card-content {
		@apply bg-white dark:bg-neutral-800
           border border-neutral-200 dark:border-neutral-700
           rounded-lg p-4
           hover:shadow-lg hover:border-blue-500 dark:hover:border-blue-400
           transition-all;
	}

	.header-row {
		@apply flex items-center gap-3 mb-3 flex-wrap;
	}

	.provision-heading {
		@apply text-base font-semibold text-neutral-900 dark:text-neutral-100;
	}

	.heading-text {
		@apply ml-2 font-normal text-neutral-700 dark:text-neutral-300;
	}

	.badges-right {
		@apply flex items-center gap-2 ml-auto;
	}

	.text-preview {
		@apply relative mb-4 text-neutral-700 dark:text-neutral-300 text-sm leading-relaxed;
		max-height: 4.5rem; /* ~3 lines */
		overflow: hidden;
	}

	.fade-overlay {
		@apply absolute bottom-0 right-0 w-24 h-6
           bg-gradient-to-r from-transparent to-white dark:to-neutral-800;
	}

	.metadata-row {
		@apply flex items-center gap-4 text-sm text-neutral-600 dark:text-neutral-400 flex-wrap;
	}
</style>
