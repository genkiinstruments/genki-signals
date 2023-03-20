<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { get } from 'svelte/store';

	import { io } from 'socket.io-client';
	import { SciChartSurface } from 'scichart/Charting/Visuals/SciChartSurface';
	import type { TSciChart } from 'scichart';

	import { getSubChartRects } from '../utils/helpers';
	import { SubChart } from '../scicharts/subchart';
	import { SCICHART_KEY } from '../utils/constants';
	import { option_store, selected_index_store } from '../stores/chart_stores';
	import { data_keys_store, data_idxs_store, type IndexRanges } from '../stores/data_stores';


	const socket = io('http://localhost:5000/');


	let el: HTMLDivElement;
	let subcharts: SubChart[] = [];

	export function remove_chart(idx: number): void {
		subcharts[idx]?.delete();
		subcharts.splice(idx, 1);
		option_store.remove_option_at(idx);
		selected_index_store.set(option_store.count() - 1); // Select the last option (-1 is a valid and handled as nothing).
	}

	// import {SciChartJSDarkTheme} from "scichart/Charting/Themes/SciChartJSDarkTheme";

    // const theme = {... new SciChartJSDarkTheme()};
    // // theme.sciChartBackground = "Transparent"
    // // theme.loadingAnimationBackground = "Transparent";


	let main_surface: SciChartSurface, wasm_context: TSciChart;
	onMount(async () => {
		SciChartSurface.setRuntimeLicenseKey(SCICHART_KEY);
		const { sciChartSurface, wasmContext } = await SciChartSurface.createSingle(el);
		main_surface = sciChartSurface;
		wasm_context = wasmContext;

		option_store.subscribe((options) => {
			const n_subcharts = subcharts.length;

			let num_columns = 1;
			const num_charts = options.length
			while(num_charts > num_columns**2) num_columns += 1;

			const rects = getSubChartRects(num_charts,
					1 / Math.ceil(num_charts / num_columns),
					1 / num_columns,
					num_columns);

			subcharts.forEach((subchart, i) => {
				subchart.set_position(rects[i])
			});


			if (n_subcharts >= options.length) return;

			for (let i = n_subcharts; i < options.length; i++) {
				const new_subchart = new SubChart('bla', main_surface, wasm_context, rects[i], structuredClone(get(options[i])));
				subcharts.push(new_subchart);

				options[i].subscribe((option) => {
					new_subchart.plot.update_all_options(structuredClone(option));
				});
			}
		});

		socket.on('data', (response) => {
			data_keys_store.set(Object.keys(response));

			const idxs_ranges: IndexRanges = {};
			get(data_keys_store).forEach((key) => {
				if (key in response) {
					idxs_ranges[key] = response[key].length;
				}
			});
			data_idxs_store.set(idxs_ranges);
			subcharts.forEach((subchart) => {
				subchart.update(response);
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

		// option_store.set([]);
	});
</script>

<div class='container'>
	<div class='remove_option_buttons'>
		<p> Remove </p>
		{#each $option_store as option, i}
			<button on:click={() => remove_chart(i)}> {i}: {get(option).description} </button>
		{/each}
	</div>

	<div bind:this={el} id={'blabla'} class='dashboard'/>
</div>

<style>
	.dashboard {
		width: 100%;
		height: 100%;
	}

	.container {
		display: flex;
		width: 70%;
	}

	.remove_option_buttons {
		width: 6%;
		display: flex;
		flex-direction: column;
		align-items: center;
		overflow-x: hidden;
		overflow-y: scroll;
	}

	.remove_option_buttons button {
		width: 100%;
	}
</style>