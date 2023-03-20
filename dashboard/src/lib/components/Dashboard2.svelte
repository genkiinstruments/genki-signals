<script lang="ts">
	import { get, type Writable } from 'svelte/store';
	import { onMount, onDestroy } from 'svelte';
	
    import type { Socket } from 'socket.io-client';

	import { SciChartSurface } from 'scichart/Charting/Visuals/SciChartSurface';
	import type { TSciChart } from 'scichart';

	import { getSubChartRects } from '../utils/helpers';
	import { SCICHART_KEY } from '../utils/constants';
	import { subchart_store, selected_subchart_store } from '../stores/chart_stores';
	import { data_keys_store, data_idxs_store, type IndexRanges } from '../stores/data_stores';
	import type { SubChart } from '../scicharts/subchart';
	import type { PlotOptions } from '$lib/scicharts/baseplot';

    let el: HTMLDivElement;


    export let socket: Socket;


	onMount(async () => {
		SciChartSurface.setRuntimeLicenseKey(SCICHART_KEY);
		const { sciChartSurface, wasmContext } = await SciChartSurface.createSingle(el);

        subchart_store.link_to_scichart_surface(sciChartSurface, wasmContext);

		socket.on('data', (response) => {
			data_keys_store.set(Object.keys(response));

			const idxs_ranges: IndexRanges = {};
			get(data_keys_store).forEach((key) => {
				if (key in response) {
					idxs_ranges[key] = response[key].length;
				}
			});
			data_idxs_store.set(idxs_ranges);

			// subchart_store.get_store()
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
</script>

<div class='container'>
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
</style>