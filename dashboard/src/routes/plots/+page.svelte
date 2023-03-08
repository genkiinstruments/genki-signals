<script lang="ts">
    import { get, writable } from 'svelte/store';

    import type { PlotOptions } from '$lib/scicharts/baseplot';
    import { option_store, selected_index_store } from '$lib/stores/chart_stores';
	import { data_keys_store, data_idxs_store } from '$lib/stores/data_stores';

	import OptionMenu from '$lib/components/OptionMenu.svelte';
	import Dashboard from '$lib/components/Dashboard.svelte';


    $: selected_index = $selected_index_store;
	$: selected_store = selected_index === -1? writable({} as PlotOptions) : $option_store[selected_index];

</script>


<div class='dashboard_layout'>
	<Dashboard selected_store={selected_store}, selected_index={selected_index}/>
	<OptionMenu selected_store={selected_store}/>
</div>

<style>
	.dashboard_layout {
		width: 100%;
		height: 1000px;
		display: flex;
		justify-content: center;
	}
</style>

