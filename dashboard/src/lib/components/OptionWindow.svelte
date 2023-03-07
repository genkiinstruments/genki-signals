<script>
	import { writable, get } from 'svelte/store';

	export let options = {};
	export let onSave = () => {};

	const options_store = writable({ ...options });

	function saveChanges() {
		onSave(get(options_store));
	}

	function appendSig(key) {
		return () => {
			const options = get(options_store);
			options[key].push({ sig_name: '', sig_idx: 0 });
			options_store.set(options);
		};
	}
</script>

<div class="option_menu">
	{#each Object.entries($options_store) as [key, value]}
		{#if typeof value === 'string' || typeof value === 'number'}
			<label>
				{key}:
				<input type="text" bind:value={$options_store[key]} required/>
			</label>
		{:else if typeof value === 'boolean'}
			<label>
				{key}:
				<input type="checkbox" bind:checked={$options_store[key]} />
			</label>
		{:else if Array.isArray(value)}
            <label>
                {key}:
                <div class="signal_menu">
					{#each value as item, idx}
						<div>
							<label>
								sig_name:
								<input type="text" bind:value={$options_store[key][idx].sig_name} />
							</label>
							<label>
								sig_idx:
								<input type="number" bind:value={$options_store[key][idx].sig_idx} />
							</label>
						</div>
					{/each}
                </div>
            </label>
            <button on:click={appendSig(key)}> Append signal </button>
		{/if}
	{/each}
	<button on:click={saveChanges}>Save changes</button>
</div>

<style>
	.option_menu {
		width: 25%;
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
