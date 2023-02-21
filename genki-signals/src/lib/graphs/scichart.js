import { SciChartSurface } from "scichart/Charting/Visuals/SciChartSurface.js";
import { NumericAxis } from "scichart/Charting/Visuals/Axis/NumericAxis.js";
import { XyDataSeries } from "scichart/Charting/Model/XyDataSeries.js";
import { XyScatterRenderableSeries } from "scichart/Charting/Visuals/RenderableSeries/XyScatterRenderableSeries.js";
import { EllipsePointMarker } from "scichart/Charting/Visuals/PointMarkers/EllipsePointMarker.js";
import { NumberRange } from "scichart/Core/NumberRange.js";

import { SCICHARTKEY } from "$lib/utils/constants.js";

/**
 * @param {String} divname - Where the SciChart will be rendered. 
 */
export async function initSciChart(divname) {
    SciChartSurface.setRuntimeLicenseKey(SCICHARTKEY);

    const { sciChartSurface, wasmContext } = await SciChartSurface.create(divname);
    // Create an X,Y Axis and add to the chart
    const xAxis = new NumericAxis(wasmContext);
    const yAxis = new NumericAxis(wasmContext);

    sciChartSurface.xAxes.add(xAxis);
    sciChartSurface.yAxes.add(yAxis);
 
    const scatterSeries = new XyScatterRenderableSeries(wasmContext, {
        pointMarker: new EllipsePointMarker(wasmContext, { width: 7, height: 7, fill: "White", stroke: "SteelBlue" }),
    });
    sciChartSurface.renderableSeries.add(scatterSeries);

    const scatterData = new XyDataSeries(wasmContext, { dataSeriesName: "Cos(x)" });
    scatterData.containsNaN = false; // Disable NaN checking for performance
    // scatterData.isSorted = true; // Performance

    scatterSeries.dataSeries = scatterData;

    xAxis.visibleRange = new NumberRange(0, 2560);
    yAxis.visibleRange = new NumberRange(1440, 0);

    return {
        sciChartSurface,
        wasmContext,
        xAxis,
        yAxis,
        scatterSeries,
        scatterData,
        update: (xs, ys) => {
            scatterData.appendRange(xs, ys);
            const count = scatterData.count();
            if (count > 100) {
                scatterData.removeRange(0, count - 100);
            }
        }
    }
}