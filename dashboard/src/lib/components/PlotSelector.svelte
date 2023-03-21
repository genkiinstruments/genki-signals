<script lang="ts">
    import PlotSelectionEntry from "$lib/components/PlotSelectionEntry.svelte"

    export let plotNames: string[];

    $: selected_index = 0
</script>

<div class = "plotSelector">
    {#each plotNames as name, i}
        <PlotSelectionEntry bind:name={name} onSelect={() => {selected_index=i}} onDelete={() => {console.log("delete")}}/>
    {/each}
</div>


<style>
    .plotSelector {
        overflow: scroll;
    }
</style>
