<script lang="ts">
    import { writable } from 'svelte/store';

    import OptionMenu from '$lib/components/OptionMenu.svelte';
    import type { PlotOptions } from '$lib/scicharts/baseplot';

    import { option_store, selected_index_store } from '$lib/stores/chart_stores';


    $: selected_index = $selected_index_store;
	$: selected_store = selected_index === -1? writable({} as PlotOptions) : $option_store[selected_index];

</script>

<OptionMenu selected_store={selected_store}/>