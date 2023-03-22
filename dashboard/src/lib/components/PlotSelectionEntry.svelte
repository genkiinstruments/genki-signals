<script lang="ts">
    import { selected_plot_idx } from "$lib/stores/plot_stores";

    export let name: string;
    export let idx: number;
    export let onDelete: () => void;

    $: styles = {
		'color': $selected_plot_idx === idx ? "#FF5F49" : "#F0F0F0",
		'hover-color': $selected_plot_idx === idx ? "#ce3c2d" : "#A5A6A5",
	};

    $: css_var_styles = Object.entries(styles)
		.map(([key, value]) => `--${key}:${value}`)
		.join(';');

</script>

<div class="plotSelectionEntry" style="{css_var_styles}">
    <button on:click={() => selected_plot_idx.set(idx)} class="plotNameButton">{name}</button>
    <button on:click={() => onDelete()} class="plotDeleteButton">X</button>
</div>

<style>
    .plotSelectionEntry {
        width: 100%;
        display: flex;
        justify-content: space-between;
        border-top-style: solid;
        border-width: thin;
        background-color: var(--color, #F0F0F0);
    }

    .plotDeleteButton {
        position: relative;
        right: 0;
        height: 100%;
        border: none;
        background: transparent;
    }

    .plotNameButton {
        text-align: left;
        height: 100%;
        width: 100%;
        border: none;
        background: transparent;
    }

    .plotSelectionEntry:hover {
        background-color: var(--hover-color, #A5A6A5);
    }
</style>
    