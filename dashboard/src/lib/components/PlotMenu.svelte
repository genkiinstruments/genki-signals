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
	<ListboxButton class="genki_button border">Add New Plot</ListboxButton>
	<ListboxOptions class="genki_list">
		{#each plot_types as plot_type}
			<ListboxOption value="" class="w100">
				<button on:click={() => add_plot(plot_type)} class="genki_button">
					{plot_type}
				</button>
			</ListboxOption>
		{/each}
	</ListboxOptions>
</Listbox>

{#if plots.length != 0}
	<Listbox bind:value={$selected_plot_idx}>
		<ListboxButton class="genki_button border">My Plots</ListboxButton>
		<ListboxOptions class="genki_list">
			{#each plots as plot,i}
				<div class="genki_button {$selected_plot_idx === i ? "selected" : ""}">
					<ListboxOption value={i} class="w100" let:selected>
						<!-- {#if selected}
							<span style = "position: relative; bottom: 0; top: 0 left: 0; padding-left: 0.75rem; display: flex">
								<CheckIcon />
							</span>
						{/if} -->
						<button on:click={() => selected_plot_idx.set(i)} class="no_border fill_right font">{plot.get_options().name}</button>
					</ListboxOption>
					<button on:click={() => delete_plot(i)} class="no_border right">X</button>
				</div>
			{/each}
		</ListboxOptions>
	</Listbox>
{/if}