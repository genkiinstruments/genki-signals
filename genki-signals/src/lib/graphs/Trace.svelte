<script>
    import { onMount } from 'svelte';
	import { create_trace } from './trace.js';
    import '$lib/utils/dtypes.js'

    /** @type {string} */
	export let id;
    /** @type {SignalID} */
    export let sig_x;
    /** @type {SignalID} */
    export let sig_y;
    /** @type {DomainConfig}*/
    export let x_domain;
    /** @type {DomainConfig}*/
    export let y_domain;
    /** @type {number} */
	export let svg_width;
    /** @type {number} */
	export let svg_height;

	/** @type {HTMLDivElement} */
	let el;

    onMount(() => {
        create_trace(el, id, sig_x, sig_y, x_domain, y_domain, svg_width, svg_height);
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