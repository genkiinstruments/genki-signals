<script>
	import { onMount, onDestroy } from 'svelte';
	import { Line } from './line';
	import { data_buffer } from '$lib/stores/data_buffer.js';

	/** @type {String} */
	export let id;
	/** @type {Function} */
	export let xAccessor;
	/** @type {Function} */
	export let yAccessor;
	/** @type {Number} */
	export let pixel_width = 720;
	/** @type {Number} */
	export let pixel_height = 480;

	/** @type {HTMLDivElement} */
	let el;

	/** @type {Object} */
	let sciChart;

	onMount(() => {
		const sciChartPromise = initSciChart(el);
		sciChartPromise.catch((err) => {
			console.error(err);
		});

		sciChartPromise.then((sci) => {
			sciChart = sci;
			data_buffer.subscribe(id, (/** @type {Object[]} */ data) => {
				const xs = data.map(xAccessor);
				const ys = data.map(yAccessor);
				sci.update(xs, ys);
			});
		});
	});

	onDestroy(() => {
		console.log('OnDestroy');
		data_buffer.unsubscribe(id);
		sciChart.destroy();
	});
</script>

<div bind:this={el} {id} style="width: {pixel_width}px; height: {pixel_height}px;" />
