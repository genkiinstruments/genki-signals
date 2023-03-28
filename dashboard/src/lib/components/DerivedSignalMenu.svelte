<script lang="ts">
    import {
	  Listbox,
	  ListboxButton,
	  ListboxOptions,
	  ListboxOption,
	  Transition,
	} from "@rgossiaux/svelte-headlessui";

    import {data_keys_store, type DerivedSignal} from "$lib/stores/data_stores"

    export let derived_signals: DerivedSignal[];
    export let add_signal: (derived_signal: DerivedSignal) => void;

    function prepare_and_add_signal(derived_signal: DerivedSignal) {
        derived_signal.args.forEach(arg => {
            if (arg.sig_idx != null){
                arg.value += ('_' + arg.sig_idx);
                delete arg.sig_idx;
            }
        });
        add_signal(derived_signal);
    }
    
    $: selected_signal = {} as DerivedSignal;
</script>


<Listbox>
	<ListboxButton class="genki_button border">Add New Derived Signal</ListboxButton>
	<ListboxOptions class="genki_list">
		{#each derived_signals as derived_signal}
			<ListboxOption value={derived_signal} class="w100">
				<button on:click={() => {selected_signal = structuredClone(derived_signal)}} class="genki_button">
					{derived_signal.sig_name}
				</button>
			</ListboxOption>
		{/each}
	</ListboxOptions>
</Listbox>

{#if selected_signal.args != null}
    <div class="option_window border">
        <p>{selected_signal.sig_name}</p>
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
                <label >
                    <select bind:value={arg.value} class="genki_select">
                        {#each $data_keys_store as sig_key}
                            <option value={sig_key}>{sig_key}</option>
                        {/each}
                    </select>
                    <input type="number" bind:value={arg.sig_idx} style = "width: 15%"/>
                    {arg.name}
                </label>
            {/if}
        {/each}
        <button on:click={() => prepare_and_add_signal(selected_signal)} class="genki_button border">Add Signal</button>
    </div>
{/if}
