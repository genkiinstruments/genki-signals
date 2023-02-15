<script>
	import { io } from 'socket.io-client';
	import { data_buffer } from '$lib/stores/data_buffer.js';
	import Trace from '$lib/graphs/Trace.svelte';

	const socket = io('ws://localhost:5000');

	const screen_width = 2560;
	const screen_height = 1440;
	const svg_width = 480;
	const svg_height = 320;
	const trace_configs = [
		{
			id: 'mouse_trace',
			sig_x: /** @type {SignalID} */ { key: 'mouse_pos', index: 0 },
			sig_y: /** @type {SignalID} */ { key: 'mouse_pos', index: 1 },
			x_range: /** @type {RangeConfig} */ { min: 0, max: svg_width, auto: false },
			y_range: /** @type {RangeConfig} */ { min: 0, max: svg_height, auto: false },
			x_domain: /** @type {DomainConfig} */ { min: 0, max: screen_width },
			y_domain: /** @type {DomainConfig} */ { min: 0, max: screen_height },
			svg_width,
			svg_height
		},
		{
			id: 'mouse_trace2',
			sig_x: /** @type {SignalID} */ { key: 'mouse_pos', index: 0 },
			sig_y: /** @type {SignalID} */ { key: 'mouse_pos', index: 1 },
			x_range: /** @type {RangeConfig} */ { min: 0, max: svg_width, auto: false },
			y_range: /** @type {RangeConfig} */ { min: svg_height, max: 0, auto: false },
			x_domain: /** @type {DomainConfig} */ { min: 0, max: screen_width },
			y_domain: /** @type {DomainConfig} */ { min: 0, max: screen_height },
			svg_width,
			svg_height
		},
		{
			id: 'random_trace',
			sig_x: /** @type {SignalID} */ { key: 'mouse_pos', index: 0 },
			sig_y: /** @type {SignalID} */ { key: 'random', index: 0 },
			x_range: /** @type {RangeConfig} */ { min: 0, max: svg_width, auto: false },
			y_range: /** @type {RangeConfig} */ { min: svg_height, max: 0, auto: false },
			x_domain: /** @type {DomainConfig} */ { min: 0, max: screen_width },
			y_domain: /** @type {DomainConfig} */ { min: -0.5, max: 1.5 },
			svg_width,
			svg_height
		}
	];

	socket.on('data', (/** @type {Object[]} */ response) => {
		data_buffer.push(response);
	});
</script>

<div class="plots">
	{#each [0] as i}
		{#each trace_configs as config}
			<Trace {...config} />
		{/each}
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
