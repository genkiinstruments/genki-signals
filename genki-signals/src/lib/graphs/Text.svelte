<script>
	import { onMount, onDestroy } from 'svelte';
	import { data_buffer } from '$lib/stores/data_buffer.js';

	/** @type {String} */
	export let id;
	/** @type {SignalID | SignalID[]} */
	export let sigs;
	/** @type {Number} */
	export let round_to = 2;

	let text = '';

	onMount(() => {
		if (typeof sigs === 'string') {
			sigs = [sigs];
		}

		data_buffer.subscribe(id, (/** @type {Object[]} */ data) => {
			const last = data[data.length - 1];
			const selected = sigs.map((sig) => {
				const val = last[sig.key][sig.index].toFixed(round_to);

				return `${sig.key}_${sig.index}: ${val}`;
			});
			text = selected.join(', ');
		});
	});

	onDestroy(() => {
		data_buffer.unsubscribe(id);
	});
</script>

<div class="text">
	<p>{text}</p>
</div>

<style>
	.text {
		width: 200px;
		display: flex;
		flex-direction: row;
		justify-content: center;
		align-items: center;
	}
</style>
