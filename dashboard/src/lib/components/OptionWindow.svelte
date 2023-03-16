
<script lang="ts">
	import { writable } from 'svelte/store';
	import type { PlotOptions } from '$lib/scicharts/baseplot';

	import { option_store, selected_index_store } from '$lib/stores/chart_stores';
	import { data_keys_store } from '$lib/stores/data_stores';
	import { SignalConfig } from '$lib/scicharts/types';


	function appendSig(key: string) {
		return () => {
			const new_sig = new SignalConfig('', 0);
			selected_store.update((store) => {
				store[key].push(new_sig);
				return store;
			});	
		};
	}
	$: dropdown_values = {
		'x_axis_align': ['top', 'bottom', 'left', 'right'],
		'y_axis_align': ['top', 'bottom', 'left', 'right'],
		'sig_x': $data_keys_store,
		'sig_y': $data_keys_store,
	}
    $: selected_index = $selected_index_store;
	$: selected_store = selected_index === -1? writable({} as PlotOptions) : $option_store[selected_index];

</script>
<div class="container">
	<div class="option_window">
		{#each Object.entries($selected_store) as [key, value]}
			{#if key === 'type'}
				<p> {key}: {value }</p>
			{:else if key === 'description'}
				<label>
					{key}:
					<input type="text" bind:value={$selected_store[key]} on:change={option_store.update_all_subscribers}/>
				</label>
			{:else}
				{#if typeof value === 'number'}
					<label>
						{key}:
						<input type="number" bind:value={$selected_store[key]} required/>
					</label>
				{:else if typeof value === 'boolean'}
					<label>
						{key}:
						<input type="checkbox" bind:checked={$selected_store[key]} />
					</label>
				{:else if typeof value === 'string'}
					<label>
						{key}:
						<select bind:value={$selected_store[key]}>
							{#each dropdown_values[key] as item}
								<option value={item}>{item}</option>
							{/each}
						</select>
					</label>
				{:else if Array.isArray(value)}
					{key}:
					<button on:click={appendSig(key)}> Add signal </button>
					<label>
						<div class="signal_menu">
							{#each value as item, idx}
								<div>
									<label>
										sig_key: 
										<br>
										<select bind:value={$selected_store[key][idx].sig_key} >
											<option value='random' selected disabled hidden>random</option>
											{#each dropdown_values['sig_x'] as item}
												<option value={item}>{item}</option>
											{/each}
										</select>
									</label>
									<label>
										sig_idx:
										<input type="number" bind:value={$selected_store[key][idx].sig_idx} />
									</label>
								</div>
							{/each}
						</div>
					</label>
				{/if}
			{/if}
		{/each}
		<!-- <button on:click={() => console.log(get(selected_store))}> Log </button> -->
	</div>
</div>
<style>
	.container {
		width: 10%;
		height: 100%;
		overflow: scroll;
	}

	.option_window {
		height: calc(100%-10px-4px);
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		padding: 10px;
		background-color: #f5f5f5;
		border: 1px solid #ccc;
		border-radius: 4px;
	}

    .signal_menu {
        display: flex;
        flex-direction: row;
        align-items: flex-start;
        flex-wrap: wrap;
    }

	label {
		display: block;
		margin-bottom: 10px;
	}

	input[type='text'],
	input[type='number'] {
		width: 100%;
		padding: 5px;
		font-size: 16px;
		border: 1px solid #ccc;
		border-radius: 4px;
		box-sizing: border-box;
	}

	button {
		margin-bottom: 5px;
	}
</style>
