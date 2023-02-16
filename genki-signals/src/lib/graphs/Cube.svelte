<script>
    import { onMount, onDestroy } from 'svelte';
	import { create_cube } from './cube.js';
    import { data_buffer } from '$lib/stores/data_buffer.js';
    import '$lib/utils/dtypes.js'

    /** @type {string} */
	export let id;
    /** @type {SignalID} */
    export let sig_rot;
    /** @type {number} */
	export let svg_width;
    /** @type {number} */
	export let svg_height;

	/** @type {HTMLDivElement} */
	let el;

    onMount(() => {
        var cube = create_cube(el, id, sig_rot, svg_width, svg_height);
        data_buffer.subscribe(
            id,
            (/** @type {Object[]} */ data) => { cube.update(data); }
        );
    });
    onDestroy(() => {
        data_buffer.unsubscribe(id);
    });
</script>


<div bind:this={el} class="line"/>


<style>
    .line {
      fill: none;
      stroke: #000;
      stroke-width: 1.5px;
    }
</style>