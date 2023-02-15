<script>
    import { onMount } from 'svelte';
	import { create_trace } from './trace.js';

    /** @type {string} */
    export let x_key;
    /** @type {string} */
    export let y_key;
    /** @type {string} */
	export let id;
    /** @type {number} */
	export let width;
    /** @type {number} */
	export let height;

	/** @type {HTMLDivElement} */
	let el;

    onMount(() => {
        create_trace(el, x_key, y_key, id, width, height);
    });


</script>


<div bind:this={el} class="trace"/>


<style>
    .trace {
      fill: none;
      stroke: #000;
      stroke-width: 1.5px;
    }
</style>