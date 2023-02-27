<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { io } from 'socket.io-client';
	import { SciChartSurface } from 'scichart/Charting/Visuals/SciChartSurface';
	import { Line } from '../scicharts/line';
	import { Rect } from 'scichart';
	import type { TSciChart } from 'scichart';

	import { getSubChartRects } from '../utils/subchart_helpers';
	import { defaultSubChartOptions } from '../scicharts/subchart';

	const socket = io('http://localhost:5000');

	let el: HTMLDivElement;

	const pixel_width = 1000;
	const pixel_height = 1000;

	let main_surface: SciChartSurface, wasm_context: TSciChart;
	let subplots: Line[] = [];
	onMount(() => {
		const sci_chart_promise = SciChartSurface.createSingle(el);
		sci_chart_promise.catch((err) => {
			console.error(err);
		});
		sci_chart_promise.then((resolve) => {
			main_surface = resolve.sciChartSurface;
			wasm_context = resolve.wasmContext;

			const rects = getSubChartRects(4, 0.2, 0.2, 2);
			const default_options = defaultSubChartOptions;
			default_options.x_domain_max = 2560;
			default_options.x_domain_min = 0;
			default_options.y_domain_max = 1440;
			default_options.y_domain_min = 0;
			default_options.y_axis_flipped = true;
			default_options.x_axis_flipped = false;
			default_options.x_axis_align = 'top';
			for (let i = 0; i < 4; i++) {
				console.log(rects[i]);
				subplots.push(new Line(`line_{i}`, main_surface, wasm_context, rects[i], default_options));
				subplots[i].create(1);
			}

			socket.on('data', (response) => {
				subplots.forEach((subplot) => {
					subplot.update(response[0], [response[1]]);
				});
			});
		});
	});
	onDestroy(() => {
		// Very important to disconnect the socket, otherwise multiple different instances of the socket
		// will be created (on open/close).
		socket.off('data');

		// Destroy the SciChartSurface
		main_surface?.delete();
		for (let i = 0; i < 4; i++) {
			subplots[i]?.delete();
		}
	});
</script>

<div bind:this={el} id={'blabla'} style="width: {pixel_width}px; height: {pixel_height}px;" />
