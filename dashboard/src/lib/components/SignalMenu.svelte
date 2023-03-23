<script lang="ts">
	import { writable } from 'svelte/store';

    import SignalEntry from './SignalEntry.svelte';

	import type { SignalConfig } from '$lib/scicharts/data';
	import type { BasePlot } from '$lib/scicharts/baseplot';
	import { selected_plot_idx } from '$lib/stores/plot_stores';
    
    export let plot: BasePlot;

    $: sig_config = plot?.get_signal_configs();

    $: x_store = sig_config != null ? writable(sig_config["sig_x"]) : writable();
    $: y_store = sig_config != null ? writable(sig_config["sig_y"]) : writable();

    function append_y_sig() {
        y_store.update(y_configs => {
            y_configs.push({key: '', idx: 0} as SignalConfig);
            return y_configs;
        });
    }

    function remove_sig(idx: number) {
        y_store.update(y_configs => {
            y_configs.splice(idx, 1);
            return y_configs;
        });
    }

    function apply_changes() {
        plot.set_signals($x_store, $y_store);
    }

</script>

<div class="signal_menu">
    <div class="entries">
        {#if $x_store != null}
            <p> Signal x </p>
            <SignalEntry bind:config={$x_store} />
        {/if}
    </div>
    <div class="entries">
        {#if $y_store != null}
            <p> Signal y </p>
            <button on:click={append_y_sig}>+</button>
            {#each $y_store as config, i}
                <div class="container">
                    <button on:click={() => remove_sig(i)}>-</button>
                    <SignalEntry bind:config={config} />
                </div>
            {/each}
        {/if}
    </div>

    <button on:click={apply_changes}> Apply changes </button>
</div>

<style>
    .signal_menu {
        display: flex;
        flex-direction: column;
        align-items: center;
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
