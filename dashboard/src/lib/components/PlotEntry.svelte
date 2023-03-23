<script lang="ts">
    import { selected_plot_idx } from "$lib/stores/plot_stores";

    export let name: string;
    export let idx: number;
    export let delete_entry: () => void;

    $: styles = {
		'color': $selected_plot_idx === idx ? "#FF5F49" : "#F0F0F0",
		'hover-color': $selected_plot_idx === idx ? "#ce3c2d" : "#A5A6A5",
	};

    $: css_var_styles = Object.entries(styles)
		.map(([key, value]) => `--${key}:${value}`)
		.join(';');

</script>

<div class="plot_entry" style="{css_var_styles}">
    <button on:click={() => selected_plot_idx.set(idx)} class="plot_name_button">{name}</button>
    <button on:click={() => delete_entry()} class="plot_delete_button">X</button>
</div>

<style>
    .plot_entry {
        width: 100%;
        display: flex;
        justify-content: space-between;
        border-top-style: solid;
        border-width: thin;
        background-color: var(--color, #F0F0F0);
    }

    .plot_delete_button {
        position: relative;
        right: 0;
        height: 100%;
        border: none;
        background: transparent;
    }

    .plot_name_button {
        text-align: left;
        height: 100%;
        width: 100%;
        border: none;
        background: transparent;
    }

    .plot_entry:hover {
        background-color: var(--hover-color, #A5A6A5);
    }
</style>
    