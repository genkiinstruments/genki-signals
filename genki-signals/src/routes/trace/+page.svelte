<script>
	import { io } from 'socket.io-client';
	import { data_buffer } from '$lib/stores/data_buffer.js';
	import Trace from '$lib/graphs/Trace.svelte';

	const socket = io('ws://localhost:5000');
	const trace_configs = [
		// {
		// 	data_key: 'mouse_pos',
		// 	id: 'trace0',
		// 	width: 200,
		// 	height: 200
		// },
		{

			x_key: 'mouse_pos_x',
			y_key: 'mouse_pos_y',
			id: 'trace1',
			width: 1920,
			height: 1080
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
