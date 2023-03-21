<script lang="ts">
	import SignalMenu from "$lib/components/SignalMenu.svelte";
    import CollapsibleMenu from "$lib/components/CollapsibleMenu.svelte";
	import PlotSelector from "$lib/components/PlotSelector.svelte";

	import { onDestroy, onMount } from "svelte";

	import { io } from 'socket.io-client';

	import { Dashboard } from "$lib/scicharts/dashboard";

    import { Signal, type SignalConfig } from "$lib/scicharts/data";
	import { SciChartSurface, type TSciChart } from "scichart";
	import { SCICHART_KEY } from '$lib/utils/constants';



    function on_save(sig_x: SignalConfig, sig_y: SignalConfig[]) {
        console.log(sig_x, sig_y);
        // Dashboard.plots[$selected_idx].set_signals(sig_x, sig_y);
    }


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

        const sig_x = new Signal('timestamp', 0);
        const sig_y = [new Signal('mouse_position', 0), new Signal('mouse_position', 1)]
        const x_config: SignalConfig = sig_x.get_config();
        const y_configs: SignalConfig[] = sig_y.map((sig) => sig.get_config());

        dashboard.plots[0]?.set_signals(x_config, y_configs);

		socket.on('data', (response) => {
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
		main_surface?.delete();
		for(let plot of dashboard) {
			plot.delete();
		};
	});

	// $: plotNames = dashboard.plots.forEach(plot => {plot.get_options().name})

</script>

<div class='container'>
    <CollapsibleMenu collapse_direction='left'>
        <span slot='header'> Menu </span>
        <span slot='body'> Body </span>
    </CollapsibleMenu>
    <div class='menu--left'>
    </div>
	<div bind:this={el} id={'blabla'} class='dashboard'/>
    <div class='menu--right'>
		<!-- <PlotSelector plotNames={plotNames}/> -->
    </div>
</div>

<style>
	.dashboard {
		width: 100%;
		height: 100%;
	}

	.container {
		display: flex;
		width: 100%;
        height: 100vh;
	}
</style>

