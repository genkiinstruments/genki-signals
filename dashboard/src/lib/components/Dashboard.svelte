<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { io } from 'socket.io-client';
	import { SciChartSurface } from 'scichart/Charting/Visuals/SciChartSurface';
	import type { TSciChart } from 'scichart';

	import { getSubChartRects } from '../utils/subchart_helpers';
	import { SubChart } from '../scicharts/subchart';
<<<<<<< HEAD:dashboard/src/lib/components/Dashboard.svelte
	import type { LinePlotOptions } from '../scicharts/line';
=======
	import { get_default_line_plot_options } from '../scicharts/line';
	import { get_default_trace_plot_options } from '../scicharts/trace';
>>>>>>> cce0048 (added trace,  n_visible_points does not work):genki-signals/src/lib/scidashboard/Dashboard.svelte
	import { SCICHART_KEY } from '../utils/constants';

	import { option_store, selected_chart_store } from '../stores/chart_stores';
	import { ChartLayoutState } from 'scichart/Charting/LayoutManager/ChartLayoutState';

	const socket = io('http://localhost:5000');
	let el: HTMLDivElement;
	let subcharts: SubChart[] = [];

	export let num_charts: number = 4;
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
		n_visible_points: 1000,
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
<<<<<<< HEAD:dashboard/src/lib/components/Dashboard.svelte
			
=======
			// const line_options = get_default_line_plot_options();
			// line_options.auto_range = true;
			// line_options.x_axis_flipped = true;
			// line_options.x_axis_visible = false;
			// line_options.data_is_sorted = true;
			// line_options.data_contains_nan = false;
			// line_options.n_visible_points = 100;
			// line_options.sig_x = [{ sig_name: 'timestamp_us', sig_idx: 0 }];
			// line_options.sig_y = [
			// 	{ sig_name: 'mouse_pos', sig_idx: 0 },
			// 	{ sig_name: 'mouse_pos', sig_idx: 1 }
			// ];

			const line_options = get_default_trace_plot_options();
			line_options.x_axis_flipped = false;
			line_options.x_axis_visible = true;
			line_options.y_axis_flipped = true;
			line_options.data_is_sorted = true;
			line_options.data_contains_nan = false;
			line_options.n_visible_points = 100;
			line_options.sig_x = [{ sig_name: 'mouse_pos', sig_idx: 0 }];
			line_options.sig_y = [{ sig_name: 'mouse_pos', sig_idx: 1 }];
			

>>>>>>> cce0048 (added trace,  n_visible_points does not work):genki-signals/src/lib/scidashboard/Dashboard.svelte

			subcharts = Array(num_charts)
				.fill(0)
				.map((_, i) => {
					option_store.update((options) => {
						options.push(line_options)
						return options;
					});
					return new SubChart('bla', main_surface, wasm_context, rects[i], line_options)
				});

			socket.on('data', (response) => {
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

		option_store.set([]);
	});
</script>

<div bind:this={el} id={'blabla'} class='dashboard'/>

<style>
	.dashboard {
		width: 1000px;
		height: 1000px;
	}
</style>