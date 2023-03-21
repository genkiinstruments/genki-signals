<script lang="ts">
    import { writable } from 'svelte/store';

    import SignalEntry from './SignalEntry.svelte';

	import type { SignalConfig } from '$lib/scicharts/data';

    export let x_config: SignalConfig;
    export let y_configs: SignalConfig[];

    export let on_save: (sig_x: SignalConfig, sig_y: SignalConfig[]) => void;

    const y_store = writable(y_configs);

    function appendSig() {
        y_store.update(y_configs => {
            y_configs.push({key: '', idx: 0} as SignalConfig);
            return y_configs;
        });
    }

    function removeSig(idx: number) {
        y_store.update(y_configs => {
            y_configs.splice(idx, 1);
            return y_configs;
        });
    }

    function apply_changes() {
        on_save(x_config, $y_store);
    }


</script>

<div class="signal_menu">
    <div class="entries">
        <p> Signal x </p>
        <SignalEntry bind:config={x_config} />
    </div>
    <div class="entries">
        <p> Signal y </p>
        <button on:click={appendSig}>+</button>
        {#each $y_store as config, i}
            <div class="container">
                <button on:click={() => removeSig(i)}>-</button>
                <SignalEntry bind:config={config} />
            </div>
        {/each}
    </div>

    <button on:click={() => apply_changes}> Apply changes </button>
</div>

<style>
    .signal_menu {
        display: flex;
        flex-direction: column;
        align-items: center;
        max-width: 10%;
        overflow-y: scroll;
        overflow-x: hidden;
        margin-left: 10px;
    }

    .entries {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 10px;
        border: 1px solid black;
    }
</style>
