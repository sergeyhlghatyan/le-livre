<script lang="ts">
	import { goto } from '$app/navigation';

	interface Props {
		provisionId: string;
		year: number;
	}

	let { provisionId, year }: Props = $props();

	function viewProvision() {
		goto(`/provision/${encodeURIComponent(provisionId)}?year=${year}`);
	}

	function openCompare() {
		goto(`/compare?provision=${encodeURIComponent(provisionId)}&year=${year}`);
	}
</script>

<div class="action-buttons flex items-center gap-2 ml-auto">
	<button onclick={viewProvision} class="btn-primary">
		View →
	</button>
	<button onclick={openCompare} class="btn-secondary">
		Compare
	</button>
</div>

<style>
	.btn-primary {
		@apply px-3 py-1.5 bg-blue-600 text-white rounded text-xs font-medium
           hover:bg-blue-700 transition-colors;
	}

	.btn-secondary {
		@apply px-3 py-1.5 border border-neutral-300 dark:border-neutral-600 rounded text-xs font-medium
           hover:bg-neutral-50 dark:hover:bg-neutral-700 transition-colors;
	}
</style>
