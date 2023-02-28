import { SciChartSurface } from 'scichart/Charting/Visuals/SciChartSurface.js';
import { NumericAxis } from 'scichart/Charting/Visuals/Axis/NumericAxis.js';
import { XyDataSeries } from 'scichart/Charting/Model/XyDataSeries.js';
import { XyScatterRenderableSeries } from 'scichart/Charting/Visuals/RenderableSeries/XyScatterRenderableSeries.js';
import { EllipsePointMarker } from 'scichart/Charting/Visuals/PointMarkers/EllipsePointMarker.js';
import { NumberRange } from 'scichart/Core/NumberRange.js';
import {
	DataPointSelectionModifier,
	ESelectionMode
} from 'scichart/Charting/ChartModifiers/DataPointSelectionModifier';
import { DataPointSelectionChangedArgs } from 'scichart/Charting/ChartModifiers/DataPointSelectionChangedArgs';
import { DataPointInfo } from 'scichart/Charting/ChartModifiers/DataPointInfo';
import { DataPointSelectionPaletteProvider } from 'scichart/Charting/Model/DataPointSelectionPaletteProvider';
import { SplineLineRenderableSeries } from 'scichart/Charting/Visuals/RenderableSeries/SplineLineRenderableSeries';
import { FastLineRenderableSeries } from 'scichart/Charting/Visuals/RenderableSeries/FastLineRenderableSeries';
import { EPointMarkerType } from 'scichart/types/PointMarkerType';
import { AUTO_COLOR } from 'scichart/Charting/Themes/IThemeProvider';
import { TextAnnotation } from 'scichart/Charting/Visuals/Annotations/TextAnnotation';
import { EHorizontalAnchorPoint } from 'scichart/types/AnchorPoint';
import { ECoordinateMode } from 'scichart/Charting/Visuals/Annotations/AnnotationBase';
import { LegendModifier } from 'scichart/Charting/ChartModifiers/LegendModifier';
import { LineSeriesDataLabelProvider } from 'scichart/Charting/Visuals/RenderableSeries/DataLabels/LineSeriesDataLabelProvider';
import { DataLabelState } from 'scichart/Charting/Visuals/RenderableSeries/DataLabels/DataLabelState';
import { SciChartJsNavyTheme } from 'scichart/Charting/Themes/SciChartJsNavyTheme';
import { MouseWheelZoomModifier } from 'scichart/Charting/ChartModifiers/MouseWheelZoomModifier';
import { ZoomExtentsModifier } from 'scichart/Charting/ChartModifiers/ZoomExtentsModifier';
import { ZoomPanModifier } from 'scichart/Charting/ChartModifiers/ZoomPanModifier';
import { RubberBandXyZoomModifier } from 'scichart/Charting/ChartModifiers/RubberBandXyZoomModifier';
import { RolloverModifier } from 'scichart/Charting/ChartModifiers/RolloverModifier';
import { EExecuteOn } from 'scichart/types/ExecuteOn';
import { Rect } from 'scichart/Core/Rect';
import { EXyDirection } from 'scichart/types/XyDirection';
import { EResamplingMode } from 'scichart/Charting/Numerics/Resamplers/ResamplingMode';
import {
	DefaultPaletteProvider,
	EStrokePaletteMode
} from 'scichart/Charting/Model/IPaletteProvider';
import { parseColorToUIntArgb } from 'scichart/utils/parseColor';

import { SCICHARTKEY } from '$lib/utils/constants.js';

// // Custom PaletteProvider for line series
class LinePaletteProvider extends DefaultPaletteProvider {
	constructor(options) {
		super();
		this.strokePaletteMode = EStrokePaletteMode.SOLID;
		if (options === null || options === void 0 ? void 0 : options.selectedLineStroke) {
			this.selectedLineStroke = (0, parseColorToUIntArgb)(
				options === null || options === void 0 ? void 0 : options.selectedLineStroke
			);
		}
		if (options === null || options === void 0 ? void 0 : options.selectedPointStroke) {
			this.selectedPointStroke = (0, parseColorToUIntArgb)(
				options === null || options === void 0 ? void 0 : options.selectedPointStroke
			);
		}
		if (options === null || options === void 0 ? void 0 : options.selectedPointFill) {
			this.selectedPointFill = (0, parseColorToUIntArgb)(
				options === null || options === void 0 ? void 0 : options.selectedPointFill
			);
		}
		this.selectedPointMarker = { stroke: this.selectedPointStroke, fill: this.selectedPointFill };
	}

	onAttached(parentSeries) {
		console.log(parentSeries.type);
	}

	overridePointMarkerArgb(xValue, yValue, index, opacity, metadata) {
		if (metadata === null || metadata === void 0 ? void 0 : metadata.isSelected) {
			return this.selectedPointMarker;
		}
		return undefined;
	}

	// This function is called for every data-point.
	// Return undefined to use the default color for the line,
	// else, return a custom colour as an ARGB color code, e.g. 0xFFFF0000 is red
	overrideStrokeArgb(xValue, yValue, index, opacity, metadata) {
		if (metadata === null || metadata === void 0 ? void 0 : metadata.isSelected) {
			return this.selectedLineStroke;
		}
		return undefined;
	}
}

const dataSize = 10000;
/** @type {number[]} */ const xValues = [];
/** @type {number[]} */ const timestamps = [];
for (let i = 0; i < dataSize; i++) {
	xValues.push(i);
	timestamps.push(100 * i);
}

/** @type {number[] | undefined} */ var lastSelected = [];

/**
 * @param {String} divname - Where the SciChart will be rendered.
 */
export async function initSciLabel(divname) {
	SciChartSurface.setRuntimeLicenseKey(SCICHARTKEY);

	const { sciChartSurface, wasmContext } = await SciChartSurface.createSingle(divname, {
		theme: new SciChartJsNavyTheme()
	});

	sciChartSurface.xAxes.add(new NumericAxis(wasmContext, { isVisible: false }));

	// Stroke/fill for selected points
	const selectedOptions = {
		selectedLineStroke: '#55FF55',
		selectedPointStroke: '#55FF55',
		selectedPointFill: '#E4F5FC'
	};

	let row_count = 4;
	let col_count = 4;

	/** @type {XyDataSeries[]} */ let dataSeries = [];
	/** @type {NumericAxis[]} */ let xAxes = [];

	for (let i = 0; i < row_count * col_count - 2; i++) {
		/** @type {number[]} */ let yValues = [Math.random() - 0.5];
		for (let i = 1; i < dataSize; i++) {
			yValues.push(yValues[i - 1] + (Math.random() - 0.5));
		}

		// Add some series onto the chart for selection
		const xyDataSeries = new XyDataSeries(wasmContext, {
			xValues,
			yValues,
			dataSeriesName: 'Series_' + i,
			metadata: timestamps.map((d) => ({ timestamp: d, isSelected: false }))
		});

		let x = (i % col_count) / col_count;
		let y = Math.floor(i / col_count) / row_count;
		console.log(i, x, y);
		let subChartSurface = sciChartSurface.addSubChart({
			position: new Rect(x, y, 1 / col_count, 1 / row_count),
			isTransparent: false
		});

		let currXAxis = new NumericAxis(wasmContext);
		xAxes.push(currXAxis);
		subChartSurface.xAxes.add(currXAxis);
		subChartSurface.yAxes.add(
			new NumericAxis(wasmContext, {
				growBy: new NumberRange(0.1, 0.1)
			})
		);

		subChartSurface.renderableSeries.add(
			new FastLineRenderableSeries(wasmContext, {
				id: 'Series' + i,
				dataSeries: xyDataSeries,
				// resamplingMode: EResamplingMode.None,
				// pointMarker: { type: EPointMarkerType.Ellipse, options: { fill: AUTO_COLOR, stroke: AUTO_COLOR, strokeThickness: 3, width: 5, height: 5 } },
				strokeThickness: 3,
				stroke: '#FFFFFF',
				// Optional visual feedback for selected points can be provided by the DataPointSelectionPaletteProvider
				// When dataSeries.metadata[i].isSelected, this still is applied
				// paletteProvider: new DataPointSelectionPaletteProvider({fill: fill, stroke: stroke }),
				paletteProvider: new LinePaletteProvider(selectedOptions)
			})
		);

		// Add the DataPointSelectonModifier to the chart.
		// selectionChanged event / callback has the selected points in the arguments
		const dataPointSelection = new DataPointSelectionModifier({
			xyDirection: EXyDirection.XDirection,
			// executeOn: EExecuteOn.MouseRightButton,
			getSelectionMode: (modifierKeys, isAreaSelection) => {
				if (modifierKeys.ctrlKey) {
					// Union when area selection and CTRL else Inverse
					return ESelectionMode.Union;
				} else if (modifierKeys.altKey) {
					// When alt Inverse
					return ESelectionMode.Inverse;
				}
				// Default mode is Replace
				return ESelectionMode.Replace;
			}
		});

		dataPointSelection.selectionChanged.subscribe((data) => {
			console.log(dataPointSelection.getAllSeries());
			/** @type {number[] | undefined} */ let currSelected = data?.selectedDataPoints.map(
				(d) => d.index
			);
			for (let series of dataSeries) {
				for (let i of lastSelected) {
					series.getMetadataAt(i).isSelected = false;
				}
				for (let i of currSelected) {
					series.getMetadataAt(i).isSelected = true;
				}
			}
			lastSelected = currSelected;
		});

		subChartSurface.chartModifiers.add(dataPointSelection);
		// subChartSurface.chartModifiers.add(new ZoomPanModifier());
		subChartSurface.chartModifiers.add(new ZoomExtentsModifier());
		subChartSurface.chartModifiers.add(
			new RolloverModifier({ modifierGroup: 'cursorGroup', showTooltip: false })
		);

		dataSeries.push(xyDataSeries);
	}

	for (let ax of xAxes) {
		ax.visibleRangeChanged.subscribe((data) => {
			sciChartSurface.xAxes.get(0).visibleRange = data.visibleRange;
		});
		sciChartSurface.xAxes.get(0).visibleRangeChanged.subscribe((data) => {
			ax.visibleRange = data.visibleRange;
		});
	}

	sciChartSurface.chartModifiers.add(new MouseWheelZoomModifier());

	return { wasmContext, sciChartSurface };
}
