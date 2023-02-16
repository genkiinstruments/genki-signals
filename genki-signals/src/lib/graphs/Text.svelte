<script>
    import { onMount, onDestroy } from 'svelte';
    import { data_buffer } from '$lib/stores/data_buffer.js';

    /** @type {string} */
    export let id;

    var text = 'Hello World';

    onMount(() => {
        data_buffer.subscribe(
            id,
            (/** @type {Object[]} */ data) => {

                const point = data[data.length-1]["mouse_pos"];
                text = `x: ${Number(point[0]).toFixed(1)}, y: ${Number(point[1]).toFixed(1)}`;
             }
        );
    });

    onDestroy(() => {
        data_buffer.unsubscribe(id);
    });
</script>

<div class="text">
    <p> {text} </p>
</div>

<style>
    .text {
        width: 200px;
        display: flex;
        flex-direction: row;
        justify-content: center;
        align-items: center;
        align-content: center;
    }
</style>
