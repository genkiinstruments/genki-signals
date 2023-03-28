<script lang="ts">
	import type { ISignalConfig } from "$lib/scicharts/signal";
    import {data_keys_store} from "$lib/stores/data_stores"

    export let config: ISignalConfig;
</script>

<div class="entry">
    <label for="signal">
        <label>
            <select bind:value={config.key} class="genki_select">
                {#each $data_keys_store as sig_key}
                    <option value={sig_key}>{sig_key}</option>
                {/each}
            </select>
            <!-- <input type="text" bind:value={config.key}/> -->
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