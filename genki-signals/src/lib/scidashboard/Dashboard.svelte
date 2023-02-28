<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { io } from 'socket.io-client';
	import { SciChartSurface } from 'scichart/Charting/Visuals/SciChartSurface';
	import type { TSciChart } from 'scichart';

	import { getSubChartRects } from '../utils/subchart_helpers';
	import { SubChart } from '../scicharts/subchart';
	import { Line, default_line_plot_options } from '../scicharts/line';
	import { SCICHART_KEY } from '../utils/constants';

	const socket = io('http://localhost:5000');

	let el: HTMLDivElement;

	const pixel_width = 1000;
	const pixel_height = 1000;

	let main_surface: SciChartSurface, wasm_context: TSciChart;
	onMount(() => {
		SciChartSurface.setRuntimeLicenseKey(SCICHART_KEY);
		const sci_chart_promise = SciChartSurface.createSingle(el);
		sci_chart_promise.catch((err) => {
			console.error(err);
		});

		sci_chart_promise.then((resolve) => {
			main_surface = resolve.sciChartSurface;
			wasm_context = resolve.wasmContext;

			const num_graphs = 1;
			const num_columns = 1;
			const rects = getSubChartRects(
				num_graphs,
				1 / (num_graphs / num_columns),
				1 / num_columns,
				num_columns
			);
			const line1_options = default_line_plot_options;
			line1_options.auto_range = false;
			line1_options.y_domain_max = 2;
			line1_options.y_domain_min = -2;
			line1_options.data_is_sorted = true;
			line1_options.data_contains_nan = false;
			line1_options.n_visible_points = 100;

			const subchart = new SubChart('bla', main_surface, wasm_context, rects[0], [line1_options]);

			socket.on('data', (response) => {
				const x = response[0];
				const y = response[1];
				subchart.update(x, [y]);
			});
		});
	});
	onDestroy(() => {
		// Very important to disconnect the socket, otherwise multiple different instances of the socket
		// will be created (on open/close).
		socket.off('data');

		// Destroy the SciChartSurface
		main_surface?.delete();
		// subchart.delete();
	});
</script>

<div bind:this={el} id={'blabla'} style="width: {pixel_width}px; height: {pixel_height}px;" />
