import { NumericAxis } from 'scichart/Charting/Visuals/Axis/NumericAxis.js';
import { XyDataSeries } from 'scichart/Charting/Model/XyDataSeries.js';
import { FastLineRenderableSeries } from 'scichart/Charting/Visuals/RenderableSeries/FastLineRenderableSeries';
import { NumberRange } from 'scichart/Core/NumberRange.js';
import { EAxisAlignment } from 'scichart';

/**
 * @param {import("scichart/Charting/Visuals/SciChartSurface").SciChartSubSurface} sciChartSurface - The SciChartSurface object in which to place this subplot.
 * @param {import("scichart").TSciChart} wasmContext - The web assembly context off the "Parent" SciChartSurface.
 * @returns {Object<Function, Function>} - Object with update and destroy functions.
 */
export function create_scichart_trace(sciChartSurface, wasmContext) {
	// Create an X,Y Axis and add to the chart
	const xAxis = new NumericAxis(wasmContext);
	xAxis.axisAlignment = EAxisAlignment.Top;
	const yAxis = new NumericAxis(wasmContext);
	yAxis.axisAlignment = EAxisAlignment.Left;

	sciChartSurface.xAxes.add(xAxis);
	sciChartSurface.yAxes.add(yAxis);

	const scatterSeries = new FastLineRenderableSeries(wasmContext);
	sciChartSurface.renderableSeries.add(scatterSeries);

	const scatterData = new XyDataSeries(wasmContext, { dataSeriesName: 'Cos(x)' });
	scatterData.containsNaN = false; // Disable NaN checking for performance
	scatterData.isSorted = true; // Performance

	scatterSeries.dataSeries = scatterData;

	//
	xAxis.visibleRange = new NumberRange(0, 2560);
	yAxis.visibleRange = new NumberRange(0, 1440);
	yAxis.flippedCoordinates = true;

	return {
		update: (/** @type {Array<Number>} */ xs, /** @type {Array<Number>} */ ys) => {
			scatterData.appendRange(xs, ys);
			const count = scatterData.count();
			if (count > 200) {
				scatterData.removeRange(0, count - 200);
			}
		},
		destroy: () => {
			sciChartSurface.delete();
			scatterData.delete();
		}
	};
}
