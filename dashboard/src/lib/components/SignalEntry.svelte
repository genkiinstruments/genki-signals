<script lang="ts">
	import type { SignalConfig } from "$lib/scicharts/data";

    export let config: SignalConfig;
</script>

<div class="entry">
    <label for="signal">
        <input type="text" bind:value={config.key} />
        <input type="number" bind:value={config.idx} />
        <input type="text" bind:value={config.name} />
    </label>
</div>

<style>
    .entry {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: space-between;
        margin: 5px;
    }
</style>