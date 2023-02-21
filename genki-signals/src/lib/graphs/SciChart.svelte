<script>
	import { onMount, onDestroy } from 'svelte';
	import { initSciChart } from './scichart.js';
	import { data_buffer } from '$lib/stores/data_buffer.js';

	const id = 'scichart';
	const divname = 'scichart-root';

	

	onMount(() => {
        const sciChartPromise = initSciChart(divname);
        sciChartPromise.catch((err) => {
            console.error(err);
        });

		sciChartPromise.then((sciChart) => {
			data_buffer.subscribe(id, (/** @type {Object[]} */ data) => {
                const xs = data.map((d) => d.mouse_pos[0]);
                const ys = data.map((d) => d.mouse_pos[1]);
				sciChart.update(xs, ys);
			});
		});
	});

	onDestroy(() => {
        console.log('OnDestroy');
		data_buffer.unsubscribe(id);
	});
</script>

<div id="scichart-root" style="width: 620px; height: 600px;" />
