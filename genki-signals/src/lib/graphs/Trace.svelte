<script>
    import { onMount } from 'svelte';

    import { data_buffer } from '$lib/stores/data_buffer.js';
	import { create_trace } from './trace.js';

    /** @type {string} */
    export let data_key;
    /** @type {string} */
	export let id;
    /** @type {number} */
	export let width;
    /** @type {number} */
	export let height;

	/** @type {HTMLDivElement} */
	let el;

    onMount(() => {
        var trace_svg = create_trace(el, data_buffer.view(), data_key, id, width, height);

        data_buffer.subscribe((/** @type {Object[]} */ data) => {
            trace_svg.update(data);
        });
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