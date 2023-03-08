
<script lang="ts">
	import { get, writable, type Writable} from 'svelte/store';
	import type { PlotOptions } from '$lib/scicharts/baseplot';

	import { option_store, selected_index_store } from '$lib/stores/chart_stores';
	import { data_keys_store } from '$lib/stores/data_stores';

	export let selected_store: Writable<PlotOptions>;

	function appendSig(key: string) {
		return () => {
			const new_sig = {'sig_name': '', 'sig_idx': 0};
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

</script>

<div class="option_window">
	{#each Object.entries($selected_store) as [key, value]}
		{#if key === 'type'}
			<p> {key}: {value }</p>
		{:else if key === 'description'}
			<label>
				{key}:
				<input type="text" bind:value={$selected_store[key]} />
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
									sig_name:
									<select bind:value={$selected_store[key][idx].sig_name}>
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

<style>
	.option_window {
		width: 65%;
		height: 1000px;
		overflow: scroll;
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		padding: 10px;
		background-color: #f5f5f5;
		border: 1px solid #ccc;
		border-radius: 4px;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.25);
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

	input[type='checkbox'] {
		margin-right: 10px;
	}

	button {
		margin-bottom: 20px;
		padding: 10px;
		background-color: #24dff3;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 16px;
	}

	button:hover {
		background-color: #0073ff;
	}
</style>
