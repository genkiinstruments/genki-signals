<script>
    import { onMount } from 'svelte';
    import { data_buffer } from '$lib/stores/data_buffer.js';

    const id = 'dataframe';

    /** @type {HTMLDivElement} */
    let el;

    onMount(() => {
        data_buffer.subscribe(
            id,
            (/** @type {Object[]} */ data) => { console.log(data); }
        );
    });
</script>

<!-- <div bind:this={el} class="dataframe">
    {#each data_buffer.view() as data}
        <p>{data.mouse_pos[0]}</p>
    {/each}
</div> -->