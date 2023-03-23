<script lang="ts">
	import PlotEntry from '$lib/components/PlotEntry.svelte';
	import type { BasePlot } from '$lib/scicharts/baseplot';

	import { selected_plot_idx } from '$lib/stores/plot_stores';

	export let plots: BasePlot[];
	export let add_plot: (type: string) => void;
	export let delete_plot: (idx: number) => void;
</script>

<div class="plot_menu">
    <div class="button_container">
        <button on:click={() => add_plot('line')} class="new_plot_button">
            New Line
        </button>
        <button on:click={() => add_plot('trace')} class="new_plot_button">
            New Trace
        </button>
        <button on:click={() => add_plot('bar')} class="new_plot_button">
            New Bar
        </button>
        <button on:click={() => add_plot('spectrogram')} class="new_plot_button">
            New Spectro
        </button>
    </div>

	{#each plots as plot, i}
		<PlotEntry
			idx={i}
			name={plot.get_options().name}
			delete_entry={() => {
				delete_plot(i);
			}}
		/>
	{/each}
</div>

<style>
	.plot_menu {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		overflow-x: auto;
		/* overflow-y: scroll; */
        border-style : solid;

		border-width: thin;

        margin-bottom: 2rem;
	}

    .button_container {
        display: flex;
        width: 100%;
        flex-direction: row;
        flex-wrap: wrap;
        justify-content: center;
        margin-bottom: 1rem;
    }

    .button_container button {
        width: 50%;
        text-align: center;
        border-style: none;
        border-top-style: solid;
        border-top-color: black;
        border-top-width: thin;
        white-space: nowrap;
    }

	.new_plot_button {
		width: 100%;
		text-align: left;
		border-style: none;
		border-top-style: solid;
		border-top-color: black;
		border-top-width: thin;
		white-space: nowrap;
	}

	.new_plot_button:hover {
		background-color: #a5a6a5;
	}
</style>
