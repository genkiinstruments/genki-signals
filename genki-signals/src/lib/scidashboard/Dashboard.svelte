<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { io } from 'socket.io-client';
	import { SciChartSurface } from 'scichart/Charting/Visuals/SciChartSurface';
	import type { TSciChart } from 'scichart';

	import { getSubChartRects } from '../utils/subchart_helpers';
	import { SubChart } from '../scicharts/subchart';
	import { get_default_line_plot_options, type LinePlotOptions } from '../scicharts/line';
	import { SCICHART_KEY } from '../utils/constants';

	const socket = io('http://localhost:5000');

	let el: HTMLDivElement;

	const pixel_width = 1440;
	const pixel_height = 1000;

	const num_charts = 2;
	const num_columns = 1;

	const line_options: LinePlotOptions = {
		type: 'line', // only line for now
        sig_x: [{ sig_name: 'timestamp_us', sig_idx: 0 }],
        sig_y: [
			{ sig_name: 'random', sig_idx: 0 },
			// { sig_name: 'mouse_pos', sig_idx: 0 },
			// { sig_name: 'mouse_pos', sig_idx: 1 },
		],
		x_axis_align: 'bottom',
		y_axis_align: 'left',
		x_axis_flipped: false,
		y_axis_flipped: false,
		x_axis_visible: false,
		y_axis_visible: true,
		data_contains_nan: false,
		data_is_sorted: false,
		auto_range: false,
		y_domain_max: 1,
		y_domain_min: 0,
		n_visible_points: 100,
	};

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


			const rects = getSubChartRects(
				num_charts,
				1 / (num_charts / num_columns),
				1 / num_columns,
				num_columns
			);


			const subcharts = Array(num_charts)
				.fill(0)
				.map((_, i) => new SubChart('bla', main_surface, wasm_context, rects[i], line_options));

			socket.on('data', (response) => {
				console.log(response);
				subcharts.forEach((subchart) => {
					subchart.update(response);
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
		// subchart.delete();
	});
</script>

<div bind:this={el} id={'blabla'} style="width: {pixel_width}px; height: {pixel_height}px;" />
