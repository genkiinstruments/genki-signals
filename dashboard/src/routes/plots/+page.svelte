<script lang="ts">
	import SignalMenu from "$lib/components/SignalMenu.svelte";
    import CollapsibleMenu from "$lib/components/CollapsibleMenu.svelte";

	import { writable } from "svelte/store";
	import { onDestroy, onMount } from "svelte";
    
	import { io } from 'socket.io-client';
    
	import { Dashboard } from "$lib/scicharts/dashboard";
	import { SciChartSurface, type TSciChart } from "scichart";

	import { SCICHART_KEY } from '$lib/utils/constants';
    import { selected_plot_idx } from "$lib/stores/plot_stores";


    const socket = io('http://localhost:5000/');

	let el: HTMLDivElement;
	let main_surface: SciChartSurface, wasm_context: TSciChart;

	let dashboard: Dashboard;

	onMount(async () => {
		SciChartSurface.setRuntimeLicenseKey(SCICHART_KEY);
		const { sciChartSurface, wasmContext } = await SciChartSurface.createSingle(el);

		main_surface = sciChartSurface;
		wasm_context = wasmContext;
        dashboard = new Dashboard(main_surface, wasm_context);

        dashboard.add_plot("line");
        dashboard.add_plot("line");
        dashboard.add_plot("line");
        dashboard.add_plot("line");


        const x_config = {key: 'timestamp', idx: 0};
        const y_configs = [{key: 'mouse_position', idx: 0}, {key: 'mouse_position', idx: 1}];

        for (let plot of dashboard) {
            plot.set_signals(x_config, y_configs);
        }

		socket.on('data', (response) => {
			for(let plot of dashboard) {
				plot.update(response);
			};
		});

	});
	onDestroy(() => {
		socket.off('data');

		main_surface?.delete();
		for(let plot of dashboard) {
			plot.delete();
		};
	});

    $: plot_store = dashboard === undefined? writable([]): dashboard.plot_store;
    selected_plot_idx.set(0);
    $: selected_plot = dashboard === undefined? undefined: $plot_store[$selected_plot_idx];
    $: store_is_defined = dashboard !== undefined;
</script>

<div class='container'>
    <div bind:this={el} id={'blabla'} class='dashboard'/>
    <CollapsibleMenu>
        <div slot='header'> Settings </div>
        <div slot='body'>
            {#if store_is_defined}
                <SignalMenu plot={selected_plot}/>
            {/if}
        </div>
    </CollapsibleMenu>
</div>

<style>
	.dashboard {
		width: 100%;
		height: 100%;
	}

	.container {
		display: flex;
		width: 100%;
        height: 80vh;
	}
</style>

