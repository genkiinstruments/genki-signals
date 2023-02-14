<script>
	import { get_socket } from '$lib/utils/socket.js';
	import { data_buffer } from '$lib/stores/data_buffer.js';
	import Trace from '$lib/graphs/Trace.svelte';

	const { socket } = get_socket('ws://localhost:5000', '/data');
	const trace_configs = [
		{
			data_key: 'mouse_pos',
			id: 'trace0',
			width: 200,
			height: 200
		},
		{
			data_key: 'mouse_pos',
			id: 'trace1',
			width: 200,
			height: 200
		}
	];

	socket.on('response', (/** @type {Object[]} */ response) => {
		data_buffer.push(response);
	});
</script>

<div class="plots">
	{#each trace_configs as config}
		<Trace {...config} />
	{/each}
</div>
