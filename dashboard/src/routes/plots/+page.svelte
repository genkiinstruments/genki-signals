<script lang="ts">
	// import Dashboard from '$lib/components/Dashboard.svelte';
	import OptionMenu from '$lib/components/OptionMenu.svelte';
	import OptionWindow from '$lib/components/OptionWindow.svelte';
	import { onMount, onDestroy } from 'svelte';
	import { get } from 'svelte/store';

	import { io } from 'socket.io-client';

	import { SciChartSurface } from 'scichart/Charting/Visuals/SciChartSurface';
	import type { TSciChart } from 'scichart';

	import { SCICHART_KEY } from '$lib/utils/constants';
	import { Dashboard } from '$lib/scicharts/dashboard';

	import { data_keys_store, data_idxs_store, type IndexRanges } from '$lib/stores/data_stores';

	const socket = io('http://localhost:5000/');

	let el: HTMLDivElement;
	let main_surface: SciChartSurface, wasm_context: TSciChart;
	let dashboard: Dashboard;

	onMount(async () => {
		SciChartSurface.setRuntimeLicenseKey(SCICHART_KEY);
		const { sciChartSurface, wasmContext } = await SciChartSurface.createSingle(el);

		main_surface = sciChartSurface;
		wasm_context = wasmContext;
		dashboard = new Dashboard(main_surface, wasm_context)

		socket.on('data', (response) => {
			data_keys_store.set(Object.keys(response));
			const idxs_ranges: IndexRanges = {};
			get(data_keys_store).forEach((key) => {
				if (key in response) {
					idxs_ranges[key] = response[key].length;
				}
			});
			data_idxs_store.set(idxs_ranges);

			for(let plot of dashboard) {
				plot.update(response);
			};
		});
	});
	onDestroy(() => {
		// Very important to disconnect the socket, otherwise multiple different instances of the socket
		// will be created (on open/close).
		socket.off('data');

		// Destroy the SciChartSurface
		main_surface.delete();
		for(let plot of dashboard) {
			plot.delete();
		};

		// option_store.set([]);
	});

</script>

<div class='dashboard_layout'>
	<!-- <Dashboard /> -->
	<OptionMenu />
	<OptionWindow />
</div>

<style>
	.dashboard_layout {
		width: 100%;
		height: 1000px;
		display: flex;
		justify-content: center;
	}


	:global(button) {
		background-color: #A5A6A5;
		color: white;
		border: none;
		border-radius: 5px;
		padding: 10px;
		cursor: pointer;
		transition: background-color 0.2s ease-in-out;
	}

    :global(button:hover) {
        background-color: #FF5F49;
    }

	:global(input) {
		background-color: #F0F0F0;
		color: black;
		border: none;
		border-radius: 5px;
		padding: 10px;
		cursor: pointer;
		transition: background-color 0.2s ease-in-out;
	}

	:global(input:hover) {
		background-color: #FF5F49;
	}

	:global(select) {
		background-color: #F0F0F0;
		color: black;
		border: none;
		border-radius: 5px;
		padding: 10px;
		cursor: pointer;
		transition: background-color 0.2s ease-in-out;
	}

	:global(select:hover) {
		background-color: #FF5F49;
	}

	:global(input[type="checkbox"]:checked) {
		accent-color: #FF5F49;
	}
</style>

