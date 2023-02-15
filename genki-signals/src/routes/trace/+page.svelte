<script>
	import { io } from 'socket.io-client';
	import { data_buffer } from '$lib/stores/data_buffer.js';
	import Trace from '$lib/graphs/Trace.svelte';

	const socket = io('ws://localhost:5000');

	const width = 720;
	const height = 480;
	const trace_configs = [
		{
			x_key: 'mouse_pos_x',
			y_key: 'mouse_pos_y',
			id: 'mouse_trace',
			width,
			height
		},
		{
			x_key: 'mouse_pos_x',
			y_key: 'random',
			id: 'random_trace',
			width,
			height
		}
	];

	socket.on('data', (/** @type {Object[]} */ response) => {
		data_buffer.push(response);
	});
</script>

<div class="plots">
	{#each trace_configs as config}
		<Trace {...config} />
	{/each}
</div>

<style>
	.plots {
		display: flex;
		flex-direction: row;
	}
</style>
