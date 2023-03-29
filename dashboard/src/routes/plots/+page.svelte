<script lang="ts">
	import SignalMenu from "$lib/components/SignalMenu.svelte";
    import CollapsibleMenu from "$lib/components/CollapsibleMenu.svelte";
	import PlotMenu from "$lib/components/PlotMenu.svelte"
	import OptionMenu from "$lib/components/OptionMenu.svelte";
	import DerivedSignalMenu from "$lib/components/DerivedSignalMenu.svelte";

	import { writable } from "svelte/store";
	import { onDestroy, onMount } from "svelte";
    
	import { io } from 'socket.io-client';

	import { SvelteDashboard } from "$lib/scicharts/svelte_dashboard";

	import { SciChartSurface, type TSciChart } from "scichart";

	import { SCICHART_KEY } from '$lib/utils/constants';
    import { selected_plot_idx } from "$lib/stores/plot_stores";

	import {data_keys_store, type DerivedSignal, type Argument} from '$lib/stores/data_stores';
 

    const socket = io('http://localhost:5000/', {
		transports: ["websocket"]
	});

	let derived_signals: DerivedSignal[] = [];
	socket.on('derived_signals', (response: Record<string, string | Record<string, string>[]>[]) => {
		derived_signals = []
		response.forEach((sig_config) => {
			if (typeof sig_config["sig_name"] !== "string") throw new Error("derived signal name must be a string")
			if (!Array.isArray(sig_config["args"])) throw new Error("arguments must be a list")
			let argList: Argument[] = [];
			sig_config["args"].forEach(arg => {
				if (arg.name && arg.type){
					argList.push({
						name: arg.name,
						type: arg.type,
						value: arg.default,
					});
				}
			});
			derived_signals.push({sig_name: sig_config["sig_name"], args: argList});
		})
	});

	let el: HTMLDivElement;
	let main_surface: SciChartSurface, wasm_context: TSciChart;

	let dashboard: SvelteDashboard;

	onMount(async () => {
		SciChartSurface.setRuntimeLicenseKey(SCICHART_KEY);
		const { sciChartSurface, wasmContext } = await SciChartSurface.createSingle(el);

		main_surface = sciChartSurface;
		wasm_context = wasmContext;
        dashboard = new SvelteDashboard(main_surface, wasm_context);

        // dashboard.add_plot("line");
        // dashboard.add_plot("line");
        // dashboard.add_plot("line");
        // dashboard.add_plot("line");


        // const x_config = {key: 'timestamp', idx: 0};
        // const y_configs = [{key: 'mouse_position', idx: 0}, {key: 'mouse_position', idx: 1}];

        // for (let plot of dashboard) {
        //     plot.set_signals(x_config, y_configs);
        // }

		socket.on('data', (response) => {
			data_keys_store.set(Object.keys(response));
			for(let plot of dashboard) {
				plot.update(response);
			};
		});

	});

	onDestroy(() => {
		socket.off('data');
		socket.off('derived_signals')

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
	<CollapsibleMenu>
		<div slot='header'> System Settings </div>
        <div slot='body'>
			<DerivedSignalMenu 
				derived_signals = {derived_signals}
				add_signal={(derived_signal) => {
					socket.emit("derived_signal", derived_signal)
				}}
			/>
		</div>
	</CollapsibleMenu>
    <div bind:this={el} id={'blabla'} class='dashboard'/>
    <CollapsibleMenu>
        <div slot='header'> Plot Settings </div>
        <div slot='body'>
			<PlotMenu plots={$plot_store}
				add_plot={(type) => {
					dashboard.add_plot(type);
					selected_plot_idx.set(dashboard.plots.length - 1);
				}} 
				delete_plot={(at) => {
					dashboard.remove_plot(at);
					if (at <= $selected_plot_idx) {
						selected_plot_idx.set(Math.max($selected_plot_idx - 1, 0));
					}
				}}
			/>
			{#if store_is_defined}
				<SignalMenu plot={selected_plot}/>
				<OptionMenu options={selected_plot?.get_options()}
					update_options={(options) => {
						selected_plot?.set_options(options);
					}}
				/>
			{/if}
		</div>
    </CollapsibleMenu>
</div>

<style>
	@import url('https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap');

	:root {
		/* font-family: 'Lato'; */
		font-family: Arial, Helvetica, sans-serif
	}

	:global(.font) {
		font: inherit;
	}

	.dashboard {
		width: 100%;
		height: 100%;
	}

	.container {
		display: flex;
		justify-content: center;
		width: 100%;
        height: 80vh;
	}

	:global(:root) {
		--genki-red: #FF5F49;
		--genki-white: #F0F0F0;
		--genki-grey: #A5A6A5;
		--genki-black: #191A18;
		--genki-red-grey: rgb(201, 67, 55);
	}

	:global(.genki_button) {
		font: inherit;
        width: 100%;
        display: flex;
        justify-content: space-between;
		text-align: left;
		border: none;
		background-color: var(--genki-white);
    }

	:global(.genki_button:hover) {
		background-color: var(--genki-grey);
	}

	:global(.selected) {
		font-weight: 700;
        background-color: var(--genki-red);
    }

	:global(.selected:hover) {
		background-color: var(--genki-red-grey);
	}

	:global(.border) {
		border: 1px solid var(--genki-grey);
		border-radius: 4px;
	}

	:global(.no_border) {
		border: none;
		background-color: inherit;
	}

	:global(.right) {
		right: 0;
	}

	:global(.w100) {
		width: 100%;
	}

	:global(.fill_right) {
		width: 100%;
		text-align: left;
	}

	:global(.genki_list) {
		font: inherit;
		list-style: none;
		padding-left: 5%;
		margin: 0%;
	}

	:global(.option_window) {
		height: calc(100%-10px-4px);
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		padding: 10px;
		background-color: var(--genki-white);
	}

	:global(.option_window *) {
		font: inherit;
		margin-bottom: 5px;
	}

	:global(.genki_select) {
		font: inherit;
	}

</style>