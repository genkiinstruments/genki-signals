<script>
	import Dashboard from '$lib/components/Dashboard.svelte';
	import OptionWindow from '$lib/components/OptionWindow.svelte';
	import { get_default_line_plot_options } from '$lib/scicharts/line';

	const options = get_default_line_plot_options();
</script>

<div class='dashboard_layout'>
	<Dashboard />
	<OptionWindow options={options}/>
</div>

<style>
	.dashboard_layout {
		display: flex;
		justify-content: space-evenly;
	}
</style>

