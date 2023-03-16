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
	.dashboard_layout {
		width: 100%;
		height: 1000px;
		display: flex;
		justify-content: center;
	}


	:global(button) {
		background-color: #A5A6A5;
		color: white;
		border: none;
		border-radius: 5px;
		padding: 10px;
		cursor: pointer;
		transition: background-color 0.2s ease-in-out;
	}

    :global(button:hover) {
        background-color: #FF5F49;
    }

	:global(input) {
		background-color: #F0F0F0;
		color: black;
		border: none;
		border-radius: 5px;
		padding: 10px;
		cursor: pointer;
		transition: background-color 0.2s ease-in-out;
	}

	:global(input:hover) {
		background-color: #FF5F49;
	}

	:global(select) {
		background-color: #F0F0F0;
		color: black;
		border: none;
		border-radius: 5px;
		padding: 10px;
		cursor: pointer;
		transition: background-color 0.2s ease-in-out;
	}

	:global(select:hover) {
		background-color: #FF5F49;
	}

	:global(input[type="checkbox"]:checked) {
		accent-color: #FF5F49;
	}
</style>

