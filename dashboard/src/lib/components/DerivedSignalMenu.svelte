<script lang="ts">
    import {
	  Listbox,
	  ListboxButton,
	  ListboxOptions,
	  ListboxOption,
	  Transition,
	} from "@rgossiaux/svelte-headlessui";

    export let derived_signals: DerivedSignal[];
    
    $: selected_signal = {} as DerivedSignal
</script>


<Listbox>
	<ListboxButton style = "width: 100%">Add New Derived Signal</ListboxButton>
	<ListboxOptions style = "list-style: none; padding: 0; width: 100%">
		{#each derived_signals as derived_signal}
			<ListboxOption value={derived_signal} style = "width: 100%">
				<button on:click={() => {selected_signal = derived_signal}} class="derived_signal">
					{derived_signal.sig_name}
				</button>
			</ListboxOption>
		{/each}
	</ListboxOptions>
</Listbox>

<div class="option_window">
    {#each selected_signal.args as arg}
        {#if arg.type === 'number'}
            <label>
                <input type="number" bind:value={arg.value} required/>
                {arg.name}
            </label>
        {:else if arg.type === 'boolean'}
            <label>
                <input type="checkbox" bind:checked={arg.value} />
                {arg.name}
            </label>
        {:else if arg.type === 'string'}
        <label>
            <input type="string" bind:value={arg.value} />
            {arg.name}
        </label>
        {:else if arg.type === "SignalName"}
        <label>
            <!-- <select bind:value={arg.value}>
            </select> -->
            {arg.name}
        </label>
        {/if}
    {/each}
</div>