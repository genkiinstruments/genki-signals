<script lang="ts">
    import PlotSelectionEntry from "$lib/components/PlotSelectionEntry.svelte"
    // import type { Writable } from "svelte/store";
    import type { BasePlot } from "$lib/scicharts/baseplot"

    import { selected_plot_idx } from "$lib/stores/plot_stores";

    export let plots: BasePlot[];
    export let onNewPlot: (type: string) => void;
    export let onDeletePlot: (idx: number) => void;
</script>

<div class = "plotSelector">
    {#each plots as plot, i}
        <PlotSelectionEntry idx={i} name={plot.get_options().name} onDelete={() => {onDeletePlot(i)}}/>
    {/each}
    <button on:click={() => {onNewPlot("line")}} class="plotSelectorButton">New Plot</button>
</div>


<style>
    .plotSelector {
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

    .plotSelectorButton {
        width: 100%;
        text-align: left;
        border-style: none;
        border-top-style: solid;
        border-top-color: black;
        border-top-width: thin;
        white-space: nowrap;
    }

    button:hover {
        background-color: #A5A6A5;
    }
</style>
