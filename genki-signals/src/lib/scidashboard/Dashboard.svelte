<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { io } from 'socket.io-client';
	import { SciChartSurface } from 'scichart/Charting/Visuals/SciChartSurface';
	import { type TSciChart, NumericAxis, EZoomState } from 'scichart';

	import { getSubChartRects } from '../utils/subchart_helpers';
	import { SubChart } from '../scicharts/subchart';
	import { get_default_line_plot_options } from '../scicharts/line';
	import { SCICHART_KEY } from '../utils/constants';
	import type { SignalConfig } from '$lib/scicharts/types';
	import { compare_signals } from '../scicharts/types';

	const socket = io('http://localhost:5000');

	let el: HTMLDivElement;

	const pixel_width = 1000;
	const pixel_height = 1000;

	let signals: Object<string, number> = {};
	let selected_signal: string;

	let main_surface: SciChartSurface, wasm_context: TSciChart;
	let mainXAxis: NumericAxis;
	let subcharts: SubChart[] = [];

	onMount(() => {
		SciChartSurface.setRuntimeLicenseKey(SCICHART_KEY);
		const sci_chart_promise = SciChartSurface.createSingle(el);
		sci_chart_promise.catch((err) => {
			console.error(err);
		});

		sci_chart_promise.then((resolve) => {
			main_surface = resolve.sciChartSurface;
			wasm_context = resolve.wasmContext;

			mainXAxis = new NumericAxis(wasm_context, {isVisible: false});
			main_surface.xAxes.add(mainXAxis);

			const num_graphs = 4;
			const num_columns = 2;
			const rects = getSubChartRects(
				num_graphs,
				1 / (num_graphs / num_columns),
				1 / num_columns,
				num_columns
			);
			const line_options = get_default_line_plot_options();
			line_options.auto_range = true;
			line_options.x_axis_flipped = false;
			line_options.x_axis_visible = false;
			line_options.data_is_sorted = true;
			line_options.data_contains_nan = false;
			line_options.n_visible_points = 100;
			line_options.sig_x = [{ sig_name: 'timestamp_us', sig_idx: 0 }];
			line_options.sig_y = [
				// { sig_name: 'random', sig_idx: 0 },
				// { sig_name: 'mouse_pos', sig_idx: 0 },
				// { sig_name: 'mouse_pos', sig_idx: 1 }
			];

			subcharts = Array(num_graphs)
				.fill(0)
				.map(
					(_, i) =>
						new SubChart(
							'subchart_' + i,
							main_surface,
							wasm_context,
							rects[i],
							structuredClone(line_options)
						)
				);

			socket.on('data', (response) => {
				if(Object.keys(response).length == 0){return;}
				if(Object.keys(signals).length == 0){
					console.log(signals)
					signals = Object.fromEntries(
						Object.entries(response).map((entry) => [entry[0], entry[1].length])
					);
				}
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
		subcharts.forEach((subchart) => subchart.delete());
	});

	function toggle_plots(sig: string, checked: boolean) {
		for (let idx of Array(signals[sig]).keys()) {
			document.getElementById(sig + '_' + idx).checked = checked;
			toggle_plot(sig, idx, checked);
		}
	}

	function toggle_plot(sig: string, idx: number, checked: boolean) {
		let sig_config = { sig_name: sig, sig_idx: idx };
		if (checked) {
			for (let subchart of subcharts) {
				subchart.plot.add_plot(sig_config, null);
			}
		} else {
			for (let subchart of subcharts) {
				subchart.plot.remove_plot(sig_config, null);
			}
		}
	}

	function live_toggle() {
		for (let subchart of subcharts) {
			const state = subchart.sub_chart_surface.zoomState^1;
			subchart.sub_chart_surface.setZoomState(state);
		}
	}

	function signal_sub_selection_toggle(sig: string) {
		let x = document.getElementById(sig + '_columns');
		if (x == null) {
			return;
		}
		if (x.style.display === 'block') {
			x.style.display = 'none';
		} else {
			x.style.display = 'block';
		}
	}
</script>

<div class="container">
	<div bind:this={el} class="dashboard" />
	<div class="signal_select">
		{#each Object.keys(signals) as sig}
			<div class="dropbtn">
				<input type="checkbox" id={sig} on:change={(a) => toggle_plots(sig, a.target?.checked)} />
				<label class="signal_selector" for={sig}>{sig}</label><br />
				<button on:click={() => signal_sub_selection_toggle(sig)}>v</button>
			</div>
			<div id="{sig}_columns" class="sub_signal_select">
				{#each Array(signals[sig]) as _, idx}
					<div>
						<input
							class="sub_signal_selector"
							type="checkbox"
							id="{sig}_{idx}"
							on:change={(a) => toggle_plot(sig, idx, a.target.checked)}
						/>
						<label for="{sig}_{idx}">{sig}_{idx}</label><br />
					</div>
				{/each}
			</div>
		{/each}
	</div>
	<div class="live">
		<button on:click={live_toggle}> Live </button>
	</div>
</div>

<style>
	.container {
		display: flex;
		flex-direction: row;
		width: 100%;
		height: 100%;
	}

	.dashboard {
		width: 70%;
		height: 100%;
	}

	.signal_select {
		width: 15%;
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		align-content: end;
	}

	.dropbtn {
		background-color: #c5c5c5;
		color: white;
		width: 50%;
		display: flex;
		flex-direction: row;
		justify-content: space-between;
	}

	.signal_selector {
		padding: 10px;
		font-size: 16px;
		color: #000;
		border: none;
		width: 90%;
		text-align: left;
	}

	.sub_signal_select {
		background-color: #c5c5c5;
		width: 50%;
		display: flex;
		flex-direction: row;
		display: none;
	}

	.sub_signal_selector {
		padding: 10px;
		margin-left: 10%;
		font-size: 14px;
		color: #000;
		border: none;
		text-align: left;
	}

	.live {
		width: 10%;
		display: flex;
		flex-direction: column;
		align-items: center;
	}
</style>
