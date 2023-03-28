<script lang="ts">
	let collapsed: boolean = false;

	function collapse() {
		collapsed = !collapsed;
	}
</script>

<div class="menu" class:collapsed>
	<div class="menu_header">
        <button on:click={collapse} class="genki_button">
            <slot name="header" />
        </button>
	</div>
	<div class="menu_body">
		<slot name="body" />
	</div>
</div>

<style>
	.menu {
        display: flex;
        flex-direction: column;
        align-items: center;
		position: relative;
		background-color: #f0f0f0;
        padding: 0 1rem;
		overflow: hidden;
		max-width: 15%;
		min-width: 1%;
		height: 100%;
		transition: all 0.3s;
	}

	.menu.collapsed {
        /* TODO: Set this so that menu header fits */
		max-width: 5%; 
	}

	.menu.collapsed .menu_body {
		opacity: 0;
		visibility: hidden;
	}

	.menu_header {
        width: 100%;
		margin-bottom: 1rem;
	}

	.menu_body {
		overflow-y: auto;
	}

	button {
		background-color: #ccc;
		border: none;
		cursor: pointer;
        width: 100%;
	}
</style>
