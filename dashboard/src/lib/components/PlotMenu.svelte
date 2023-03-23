<script lang="ts">
    import PlotEntry from "$lib/components/PlotEntry.svelte"
    import type { BasePlot } from "$lib/scicharts/baseplot"

    import { selected_plot_idx } from "$lib/stores/plot_stores";

    export let plots: BasePlot[];
    export let add_plot: (type: string) => void;
    export let delete_plot: (idx: number) => void;
</script>

<div class = "plot_menu">
    {#each plots as plot, i}
        <PlotEntry idx={i} name={plot.get_options().name} delete_entry={() => {delete_plot(i)}}/>
    {/each}
    <button on:click={() => {add_plot("line")}} class="new_plot_button">New Plot</button>
</div>


<style>
    .plot_menu
 {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        overflow-x: auto;
        /* overflow-y: scroll; */
        border-left-style: solid;
        border-right-style: solid;
        border-bottom-style: solid;
        border-width: thin;
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
        background-color: #A5A6A5;
    }
</style>