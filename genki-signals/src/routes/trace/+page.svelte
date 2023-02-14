<script>
    import { get_socket } from '$lib/utils/socket.js';
    import Trace from '$lib/graphs/Trace.svelte';

    /**
	 * @type {Object[]}
	 */
    let data = [];
    let num_keep= 1000;
    const { socket } = get_socket('ws://localhost:5000', '/data');
    const trace_configs = [
        {
            bound_data: data,
            data_key: 'mouse_pos',
            id: 'trace0',
            width: 200,
            height: 200,
            update: () => {},
        },
        {
            bound_data: data,
            data_key: 'mouse_pos',
            id: 'trace1',
            width: 200,
            height: 200,
            update: () => {},
        },
    ];

    // @ts-ignore
    socket.on("response", (/** @type {Object[]} */ response) => {
      data.push.apply(data, response);
      data.splice(0, data.length - num_keep);
    }
    );
</script>

<div class='plots'>
    {#each trace_configs as config}
        <Trace {...config} bind:update={config} />
    {/each}
</div>
