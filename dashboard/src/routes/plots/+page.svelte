<script lang="ts">
	import SignalMenu from "$lib/components/SignalMenu.svelte";
    import CollapsibleMenu from "$lib/components/CollapsibleMenu.svelte";
	import PlotSelector from "$lib/components/PlotSelector.svelte"

	import { onDestroy, onMount } from "svelte";

	import { io } from 'socket.io-client';

	import { SvelteDashboard } from "$lib/scicharts/svelteDashboard";

	import { SciChartSurface, type TSciChart } from "scichart";
	import { SCICHART_KEY } from '$lib/utils/constants';
    import type { SignalConfig } from "$lib/scicharts/data";
	import { get, writable } from "svelte/store";


    function on_save(sig_x: SignalConfig, sig_y: SignalConfig[]) {
        console.log(sig_x, sig_y);
        // Dashboard.plots[$selected_idx].set_signals(sig_x, sig_y);
    }


    const socket = io('http://localhost:5000/');

	let el: HTMLDivElement;
	let main_surface: SciChartSurface, wasm_context: TSciChart;

	let dashboard: SvelteDashboard;

	onMount(async () => {
		SciChartSurface.setRuntimeLicenseKey(SCICHART_KEY);
		const { sciChartSurface, wasmContext } = await SciChartSurface.createSingle(el);

		main_surface = sciChartSurface;
		wasm_context = wasmContext;
        dashboard = new SvelteDashboard(main_surface, wasm_context);

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

	$: plots = dashboard === undefined ? writable([]) : dashboard.plot_store;

    const x_c = {key: 'timestamp', idx: 0};
    const y_c = [{key: 'mouse_position', idx: 0}, {key: 'mouse_position', idx: 1}];

</script>

<div class='container'>
    <CollapsibleMenu>
        <div slot='header'> Additional </div>
        <div slot='body'>
            <SignalMenu x_config={x_c} y_configs={y_c} on_save={on_save}/>
        </div>
    </CollapsibleMenu>
	<div bind:this={el} id={'blabla'} class='dashboard'/>
    <CollapsibleMenu>
        <div slot='header'> Plot Settings </div>
        <div slot='body'>
            <PlotSelector plots={$plots} onNewPlot={(type) => dashboard.add_plot(type)} onDeletePlot={(at) => dashboard.remove_plot(at)}/>
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
		justify-content: center;
		width: 100%;
        height: 100%;
		overflow: hidden;
	}
</style>