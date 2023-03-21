<script lang="ts">
	import { slide } from 'svelte/transition';

	export let collapse_direction: 'left' | 'right' | 'top' | 'bottom';

	let collapsed: boolean = false;
	let collapse_class: string = 'collapsed';

	function collapse() {
		collapsed = !collapsed;
		collapse_class = collapsed ? 'collapsed' : '';
	}
</script>

<div class="menu" class:collapsed>
	<button on:click={collapse}>x</button>
	<div class="menu_header">
		<slot name="header" />
	</div>
	<div class="menu_body" in:slide={{ duration: 300 }} out:slide={{ duration: 300 }}>
		<slot name="body" />
	</div>
</div>

<style>
	.menu {
        display: flex;
        flex-direction: column;
		position: relative;
		background-color: #f0f0f0;
		padding: 1rem;
		overflow: hidden;
        max-width: 15%;
        min-width: 1%;
        width: 15%;
		height: 100%;
	}

    .menu.collapsed {
        width: 0%;
    }

	.menu.collapsed .menu_header {
		display: none;
	}

    .menu.collapsed .menu_body {
        display: none;
    }

	.menu_header {
		margin-bottom: 1rem;
	}

	.menu_body {
		overflow-y: auto;
	}

	button {
		position: absolute;
		top: 0;
		right: 0;
		background-color: #ccc;
		border: none;
		cursor: pointer;
	}
</style>
