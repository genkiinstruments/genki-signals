<!-- <script lang="ts">
	import PlotEntry from '$lib/components/PlotEntry.svelte';
	import type { BasePlot } from '$lib/scicharts/baseplot';

	import { selected_plot_idx } from '$lib/stores/plot_stores';

	export let plots: BasePlot[];
	export let add_plot: (type: string) => void;
	export let delete_plot: (idx: number) => void;
</script>

<div class="plot_menu">
    <div class="button_container">
        <button on:click={() => add_plot('line')} class="new_plot_button">
            New Line
        </button>
        <button on:click={() => add_plot('trace')} class="new_plot_button">
            New Trace
        </button>
        <button on:click={() => add_plot('bar')} class="new_plot_button">
            New Bar
        </button>
        <button on:click={() => add_plot('spectrogram')} class="new_plot_button">
            New Spectro
        </button>
    </div>

	{#each plots as plot, i}
		<PlotEntry
			idx={i}
			name={plot.get_options().name}
			delete_entry={() => {
				delete_plot(i);
			}}
		/>
	{/each}
</div>

<style>
	.plot_menu {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		overflow-x: auto;
		/* overflow-y: scroll; */
        border-style : solid;

		border-width: thin;

        margin-bottom: 2rem;
	}

    .button_container {
        display: flex;
        width: 100%;
        flex-direction: row;
        flex-wrap: wrap;
        justify-content: center;
        margin-bottom: 1rem;
    }

    .button_container button {
        width: 50%;
        text-align: center;
        border-style: none;
        border-top-style: solid;
        border-top-color: black;
        border-top-width: thin;
        white-space: nowrap;
    }

	.new_plot_button {
		width: 100%;
		text-align: left;
		border-style: none;
		border-top-style: solid;
		border-top-color: black;
		border-top-width: thin;
		white-space: nowrap;
	}

	.new_plot_button:hover {
		background-color: #a5a6a5;
	}
</style> -->

<script lang="ts">
	import {
	  Listbox,
	  ListboxButton,
	  ListboxOptions,
	  ListboxOption,
	  Transition,
	} from "@rgossiaux/svelte-headlessui";
	import { CheckIcon } from "@rgossiaux/svelte-heroicons/solid";
  
	import { selected_plot_idx } from '$lib/stores/plot_stores';
	import PlotEntry from '$lib/components/PlotEntry.svelte';
	import type { BasePlot } from '$lib/scicharts/baseplot';

	export let plots: BasePlot[];
	export let add_plot: (type: string) => void;
	export let delete_plot: (idx: number) => void;

	const plot_types= [
		'line',
		'trace',
		'bar',
		'spectrogram',
	]
</script>

<Listbox>
	<ListboxButton style = "width: 100%">Add New Plot</ListboxButton>
	<ListboxOptions style = "list-style: none; padding: 0; width: 100%">
		{#each plot_types as plot_type}
			<ListboxOption value="" style = "width: 100%">
				<button on:click={() => add_plot(plot_type)} class="plot_entry">
					{plot_type}
				</button>
			</ListboxOption>
		{/each}
	</ListboxOptions>
</Listbox>

{#if plots.length != 0}
	<Listbox bind:value={$selected_plot_idx}>
		<ListboxButton style = "width: 100%">{plots[$selected_plot_idx] ? plots[$selected_plot_idx]?.get_options().name : "Plots"}</ListboxButton>
		<ListboxOptions style = "list-style: none; padding: 0">
			{#each plots as plot,i}
				<div class={$selected_plot_idx === i ? "plot_entry_selected" : "plot_entry"}>
					<ListboxOption value={i} style = "width: 100%" let:selected>
						<!-- {#if selected}
							<span style = "position: relative; bottom: 0; top: 0 left: 0; padding-left: 0.75rem; display: flex">
								<CheckIcon />
							</span>
						{/if} -->
						<button on:click={() => selected_plot_idx.set(i)} class="plot_name_button">{plot.get_options().name}</button>
					</ListboxOption>
					<button on:click={() => delete_plot(i)} class="plot_delete_button">X</button>
				</div>
			{/each}
		</ListboxOptions>
	</Listbox>
{/if}

<style>
	.plot_entry {
        width: 100%;
        display: flex;
        justify-content: space-between;
		background-color: var(--genki-white);
    }

	.plot_entry:hover {
		background-color: var(--genki-grey);
	}

	.plot_entry_selected {
        width: 100%;
        display: flex;
        justify-content: space-between;
        background-color: var(--genki-red);
		font: bold;
    }

	.plot_entry_selected:hover {
		background-color: var(--genki-red-grey);
	}

	.plot_name_button {
		width: 100%;
		font: inherit;
		background-color: inherit;
		text-align: left;
		border: none;
	}

	.plot_delete_button {
		right: 0;
		border: none;
		background-color: inherit;
	}
</style>

<!-- 
<script lang="ts">
	import {
		Popover,
		PopoverButton,
		PopoverPanel,
	} from "@rgossiaux/svelte-headlessui";

	import { selected_plot_idx } from '$lib/stores/plot_stores';
	import PlotEntry from '$lib/components/PlotEntry.svelte';
	import type { BasePlot } from '$lib/scicharts/baseplot';

	export let plots: BasePlot[];
	export let add_plot: (type: string) => void;
	export let delete_plot: (idx: number) => void;
</script>

	<Popover style="position: relative;">
		<PopoverButton>Plots</PopoverButton>

		<PopoverPanel>
			{#each plots as plot, i}
				<PlotEntry
					idx={i}
					name={plot.get_options().name}
					delete_entry={() => {
						delete_plot(i);
					}}
				/>
			{/each}
		</PopoverPanel>
	</Popover>

<style>
	.panel-contents {
		display: grid;
		grid-template-columns: repeat(1, minmax(0, 1fr));
	}
</style> -->