<script lang="ts">
	import type { ISignalConfig } from "$lib/scicharts/signal";

    export let config: ISignalConfig;
</script>

<div class="entry">
    <label for="signal">
        <label>
            <input type="text" bind:value={config.key}/>
            Signal key
        </label>
        <label>
            <input type="number" bind:value={config.idx} />
            Signal idx
        </label>
        <label>
            <input type="text" bind:value={config.name} />
            Display Name
        </label>
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