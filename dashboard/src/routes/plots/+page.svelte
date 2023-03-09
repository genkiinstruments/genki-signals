<script lang="ts">
	import Dashboard from '$lib/components/Dashboard.svelte';
	import OptionMenu from '$lib/components/OptionMenu.svelte';
	import OptionWindow from '$lib/components/OptionWindow.svelte';

</script>

<div class='dashboard_layout'>
	<Dashboard />
	<OptionMenu />
	<OptionWindow />
</div>

<style>
	:global(body) {
		/* background: radial-gradient(circle, rgb(60, 60, 63) 0%, rgb(28, 28, 30) 100%); */
		/* background-color: black; */
	}

	.dashboard_layout {
		width: 100%;
		height: 1000px;
		display: flex;
		justify-content: center;
	}


	:global(button) {
		background-color: #24dff3;
		color: #fff;
		border: none;
		border-radius: 5px;
		padding: 10px;
		cursor: pointer;
		transition: background-color 0.2s ease-in-out;
	}

    :global(button:hover) {
        background-color: #0073ff;
    }
</style>

