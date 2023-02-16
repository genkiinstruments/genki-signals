<script>
	import { onMount, onDestroy } from 'svelte';
	import { io } from 'socket.io-client';
	import { data_buffer } from '$lib/stores/data_buffer.js';
	import Trace from '$lib/graphs/Trace.svelte';
	import Line from '$lib/graphs/Line.svelte';
	import { max } from 'd3';

	const screen_width = 2560;
	const screen_height = 1440;
	const svg_width = 480;
	const svg_height = 320;
	/**
	 * @type {Object[]}
	 */
	const trace_configs = [];
	/**
	 * @type {Object[]}
	 */
	 const line_configs = [];


	for (let i = 0; i < 5; i++) {
		trace_configs.push({
			id: `mouse_trace_${i}`,
			sig_x: /** @type {SignalID} */ { key: 'mouse_pos', index: 0 },
			sig_y: /** @type {SignalID} */ { key: 'mouse_pos', index: 1 },
			x_domain: /** @type {DomainConfig} */ { min: 0, max: screen_width, auto: false },
			y_domain: /** @type {DomainConfig} */ { min: 0, max: screen_height, auto: false },
			svg_width,
			svg_height
		});
	}

	for (let i = 0; i < 5; i++) {
		line_configs.push({
			id: `mouse_line_${i}`,
			sig_x: /** @type {SignalID} */ { key: 'timestamp_us', index: 0 },
			sig_y: /** @type {SignalID} */ [
				{ key: 'mouse_pos', index: 0 },
				{ key: 'mouse_pos', index: 1 }
			],
			x_domain: /** @type {DomainConfig} */ { min: 0, max: screen_width, auto: false },
			y_domain: /** @type {DomainConfig} */ { min: 0, max: max([screen_height, screen_width]), auto: false },
			svg_width,
			svg_height
		});
	}

	const socket = io('http://localhost:5000');

	onMount(() => {
		socket.on('data', (/** @type {Object[]} */ response) => {
			data_buffer.push(response);
		});
	});
	onDestroy(() => {
		// Very important to disconnect the socket, otherwise multiple different instances of the socket 
		// xw(on open/close) will be created which will the buffer with duplicates and lags the system.
		socket.off('data');
		data_buffer.clear();
	});
</script>

<div class="plots">
	{#each trace_configs as config}
		<Trace {...config} />
	{/each}
	{#each line_configs as config}
		<Line {...config} />
	{/each}
</div>

<style>
	.plots {
		display: flex;
		flex-direction: row;
		justify-content: space-around;
		flex-wrap: wrap;
	}
</style>
