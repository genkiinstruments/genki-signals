<script lang="ts">
    import type { PlotOptions } from '$lib/scicharts/baseplot';

    export let options: PlotOptions;
    export let update_options: (options: PlotOptions) => void

    const dropdown_values = {
		'x_axis_align': ['top', 'bottom', 'left', 'right'],
		'y_axis_align': ['top', 'bottom', 'left', 'right'],
    }
    $: update_options(options);
</script>

{#if options != null}
    <div class="option_window">
        {#each Object.entries(options) as [key, value]}
            {#if typeof value === 'number'}
                <label>
                    <input type="number" bind:value={options[key]} required/>
                    {key}
                </label>
            {:else if typeof value === 'boolean'}
                <label>
                    <input type="checkbox" bind:checked={options[key]} />
                    {key}
                </label>
            {:else if key in dropdown_values}
                <label>
                    <select bind:value={options[key]}>
                        {#each dropdown_values[key] as item}
                            <option value={item}>{item}</option>
                        {/each}
                    </select>
                    {key}
                </label>
            {:else if typeof value === 'string'}
            <label>
                <input type="string" bind:value={options[key]} />
                {key}
            </label>
            {/if}
        {/each}
    </div>
{/if}

<style>
    .option_window {
		height: calc(100%-10px-4px);
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		padding: 10px;
		background-color: var(--genki-white);
		border: 1px solid var(--genki-grey);
		border-radius: 4px;
	}
</style>
