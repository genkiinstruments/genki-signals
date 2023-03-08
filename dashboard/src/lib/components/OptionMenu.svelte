<script lang="ts">
	import { writable, get, type Writable } from 'svelte/store';

	import type { PlotOptions } from '$lib/scicharts/baseplot';
	import { get_default_line_plot_options } from '$lib/scicharts/line';
	import { get_default_trace_plot_options } from '$lib/scicharts/trace';
    import { get_default_bar_plot_options } from '$lib/scicharts/barplot';
    import { option_store, selected_index_store } from '$lib/stores/chart_stores';

	import OptionWindow from './OptionWindow.svelte';

    export let selected_store: Writable<PlotOptions>;


    function change_selected(idx: number) {
        selected_index_store.set(idx);
    }

    function add_option(type: string) {
        let new_options: PlotOptions;
        if (type === 'line') {
            new_options = get_default_line_plot_options();
            new_options.description = 'New line plot';
        }
        else if (type === 'trace') {
            new_options = get_default_trace_plot_options();
            new_options.description = 'New trace plot';
        } 
        else if (type === 'bar') {
            new_options = get_default_bar_plot_options();
            new_options.description = 'New bar plot';
        }
        else {
            throw new Error('Invalid option type');
        }

        return () => {
            option_store.add_option(structuredClone(new_options)); // Not enough to spread the object
            const idx = option_store.count()-1;
            change_selected(idx);
        };
    }
</script>

<div class="option_menu">
	<div class="options_list">
        <button on:click={add_option('line')}>
            Add line plot
        </button>
        <button on:click={add_option('trace')}>
            Add trace plot
        </button>
        <button on:click={add_option('bar')}>
            Add bar plot
        </button>

		<ul>
			{#each $option_store as store, idx}
				<li>
					<button on:click={() => change_selected(idx)}>
						{idx}: {get(store).description}
					</button>
				</li>
			{/each}
		</ul>
	</div>
    <OptionWindow selected_store={selected_store}/>
</div>

<style>
	.option_menu {
		display: flex;
        justify-content: space-evenly;
		width: 20%;
		height: 100%;
		box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2);
        margin-left: 10px;
	}

    .options_list {
        display: flex;
        flex-direction: column;
        align-items: center;
        overflow: scroll;
    }

	.options_list ul {
		list-style-type: none;
		padding: 0;
	}

	.options_list li {
        display: flex;
        justify-content: center;
		padding: 10px;
        margin: 5px;
		background-color: #fff;
		border-radius: 10px;
		transition: background-color 0.2s ease-in-out;
	}

	.options_list li:hover {
		background-color: #f9f9f9;
	}

	.options_list button {
        width: 100%;
		background-color: #24dff3;
		color: #fff;
		border: none;
		border-radius: 5px;
		padding: 10px 15px;
		cursor: pointer;
		transition: background-color 0.2s ease-in-out;
	}

	.options_list button:hover {
		background-color: #0073ff;
	}
</style>
