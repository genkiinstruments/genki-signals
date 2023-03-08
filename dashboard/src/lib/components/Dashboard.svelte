<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { io } from 'socket.io-client';
	import { SciChartSurface } from 'scichart/Charting/Visuals/SciChartSurface';
	import type { TSciChart } from 'scichart';

	import { getSubChartRects } from '../utils/subchart_helpers';
	import { SubChart } from '../scicharts/subchart';
	import type { LinePlotOptions } from '../scicharts/line';
	import type { SpectrogramPlotOptions } from '../scicharts/spectrogram';
	import { SCICHART_KEY } from '../utils/constants';

	import { option_store, selected_chart_store } from '../stores/chart_stores';
	import { ChartLayoutState } from 'scichart/Charting/LayoutManager/ChartLayoutState';

	const socket = io('http://localhost:5000');
	let el: HTMLDivElement;
	let subcharts: SubChart[] = [];

	export let num_charts: number = 2;
	const num_columns = 1;

	const line_options: LinePlotOptions = {
		type: 'line', // only line for now
        sig_x: [{ sig_name: 'timestamp_us', sig_idx: 0 }],
        sig_y: [
			{ sig_name: 'mouse_position', sig_idx: 0 },
			{ sig_name: 'mouse_position', sig_idx: 1 },
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
		y_domain_max: 0,
		y_domain_min: 2560,
		n_visible_points: 1000,
	};

	const spectrogram_options: SpectrogramPlotOptions = {
		type: 'spectrogram',
        sig_x: [],
        sig_y: [
			{ sig_name: 'accFourier', sig_idx: 0}
			// { sig_name: 'mouse_pos', sig_idx: 0 },
			// { sig_name: 'mouse_pos', sig_idx: 1 },
		],
		x_axis_align: 'bottom',
		y_axis_align: 'left',
		x_axis_flipped: false,
		y_axis_flipped: false,
		x_axis_visible: false,
		y_axis_visible: true,
		data_is_sorted: false,
		data_contains_nan: false,
		bin_count: 129,
		n_visible_windows: 8000,
		colormap_min: 0,
		colormap_max: 5,
	};

	const plotOptions = [line_options, spectrogram_options];

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
			

			subcharts = Array(num_charts)
				.fill(0)
				.map((_, i) => {
					option_store.update((options) => {
						options.push(plotOptions[i])
						return options;
					});
					return new SubChart('bla', main_surface, wasm_context, rects[i], plotOptions[i])
				});

			socket.on('data', (response) => {
				if(Object.keys(response).length == 0) {return;}
				console.log(response)
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