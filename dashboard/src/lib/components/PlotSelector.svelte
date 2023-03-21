<script lang="ts">
    import PlotSelectionEntry from "$lib/components/PlotSelectionEntry.svelte"

    export let plotNames: string[];

    $: selected_index = 0
</script>


<!-- <nav>
    <ul>
        {#each plotNames as name, i}
        <PlotSelectionEntry bind:name={name} onSelect={() => {selected_index=i}} onDelete={() => {return}}/>
        {/each}
    </ul>
</nav> -->

<div class = "plotSelector">
    {#each plotNames as name, i}
        <PlotSelectionEntry bind:name={name} onSelect={() => {selected_index=i}} onDelete={() => {return}}/>
    {/each}
</div>


<style>
    .plotSelector {
        overflow: scroll;
    }
</style>
