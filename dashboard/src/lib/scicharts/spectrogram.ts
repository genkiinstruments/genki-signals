import {
	EAutoRange,
	NumericAxis,
	SciChartSubSurface,
	SciChartSurface,
    UniformHeatmapDataSeries,
    UniformHeatmapRenderableSeries,
    HeatmapColorMap,
	type TSciChart,
    ENumericFormat,
    zeroArray2D,
    MouseWheelZoomModifier,
    ZoomPanModifier,
    ZoomExtentsModifier,
    NumberRange,
} from 'scichart';

import { BasePlot, get_default_plot_options, type PlotOptions } from './baseplot';
import type { IArrayDict} from './interfaces';
import type { ISignalConfig } from './signal';

export interface SpectrogramPlotOptions extends PlotOptions {
    window_size: number;
    sampling_rate: number;
	n_visible_windows: number;
    colormap_min: number;
    colormap_max: number;
}
export function get_default_spectrogram_plot_options(): SpectrogramPlotOptions {
	return {
		...get_default_plot_options(),
        name: 'Spectrogram',
        window_size: 256,
        sampling_rate: 100,
		n_visible_windows: 100,
        colormap_min: 0,
        colormap_max: 1,
	};
}

export class Spectrogram extends BasePlot {
	x_axis: NumericAxis;
	y_axis: NumericAxis;
	options: SpectrogramPlotOptions;

    window_size: number;
    sampling_rate: number;
    bin_count: number;

    z_values: number[][];

	renderable_series: UniformHeatmapRenderableSeries[] = [];
	data_series: UniformHeatmapDataSeries[] = [];

	constructor(
		wasm_context: TSciChart,
		surface: SciChartSubSurface,
		plot_options: SpectrogramPlotOptions = get_default_spectrogram_plot_options(),
        sig_x_config: ISignalConfig = { key: '', idx: 0 },
        sig_y_config: ISignalConfig[] = []
	) {
		super(wasm_context, surface, sig_x_config, sig_y_config);

		this.x_axis = new NumericAxis(this.wasm_context, {
            autoRange: EAutoRange.Never,
            drawLabels: false,
            drawMinorTickLines: false,
            drawMajorTickLines: false,
        });
		this.y_axis = new NumericAxis(this.wasm_context, {
            autoRange: EAutoRange.Never,
            drawMinorTickLines: false,
            drawMajorTickLines: false,
        });

		this.surface.xAxes.add(this.x_axis);
		this.surface.yAxes.add(this.y_axis);

		this.options = plot_options;

        this.window_size = this.options.window_size
        this.sampling_rate = this.options.sampling_rate
        this.bin_count = Math.floor(this.window_size/2) + 1;

        this.z_values = this.create_empty_2d();

        this.surface.chartModifiers.add(new MouseWheelZoomModifier());
        this.surface.chartModifiers.add(new ZoomPanModifier());
        this.surface.chartModifiers.add(new ZoomExtentsModifier());


		this.add_renderable();

		this.update_axes_alignment();
		this.update_axes_flipping();
		this.update_axes_visibility();
	}

    private create_empty_2d(): number[][] {
        return zeroArray2D([this.bin_count, this.options.n_visible_windows])
    }

	public update(data: IArrayDict): void {
		if (this.sig_y.length !== 1) return; // if no x signal is defined, then we can't update the plot

        const sig_key = this.sig_y[0].key;
		if (!(sig_key in data)) throw new Error(`sig_key ${sig_key} not in data`);

        if(data[sig_key][0].length == 0) return; // no new data

        this.z_values = this.z_values.map((row, i) => row.concat(data[sig_key][i]).slice(-this.options.n_visible_windows))

        this.data_series[0].setZValues(this.z_values);
	}

	protected add_renderable(at: number = -1): void {
        if (this.renderable_series.length > 0) return;

        this.data_series[0]?.delete();
        this.renderable_series[0]?.delete();
        this.data_series = [];
        this.renderable_series = [];
		const renderable_series = new UniformHeatmapRenderableSeries(this.wasm_context, {
            colorMap: new HeatmapColorMap({
                minimum: this.options.colormap_min,
                maximum: this.options.colormap_max,
                gradientStops: [
                    {offset: 0, color: "#000000"},
                    {offset: 0.25, color: "#800080"},
                    {offset: 0.5, color: "#FF0000"},
                    {offset: 0.75, color: "#FFFF00"},
                    {offset: 1, color: "#FFFFFF"}
                ]
            }),
            dataLabels: {
                numericFormat: ENumericFormat.NoFormat,
                precision: 10,
            }
        });
        this.z_values = this.create_empty_2d();
		const data_series = new UniformHeatmapDataSeries(this.wasm_context, {
            xStart: 0,
            xStep: 1,
            yStart: 0,
            yStep: this.options.sampling_rate/this.options.window_size,
            zValues: this.z_values
        });

		renderable_series.dataSeries = data_series;

		this.surface.renderableSeries.add(renderable_series);
		this.renderable_series.push(renderable_series);
		this.data_series.push(data_series);

        this.x_axis.visibleRange = new NumberRange(0, this.options.n_visible_windows);
        this.y_axis.visibleRange = new NumberRange(0, (this.bin_count-1) * this.options.sampling_rate/this.options.window_size);
        this.x_axis.visibleRangeLimit = this.x_axis.visibleRange;
        this.y_axis.visibleRangeLimit = this.y_axis.visibleRange;
	}

    private update_color_gradient(){
        this.renderable_series[0].colorMap = new HeatmapColorMap({
            minimum: this.options.colormap_min,
            maximum: this.options.colormap_max,
            gradientStops: [
                {offset: 0, color: "#000000"},
                {offset: 0.05, color: "#800080"},
                {offset: 0.2, color: "#FF0000"},
                {offset: 0.5, color: "#FFFF00"},
                {offset: 1, color: "#FFFFFF"}
            ]
        })
    }

    public update_all_options(options: SpectrogramPlotOptions): void {
        this.options = options;

        this.bin_count = Math.floor(this.window_size/2) + 1; // Should bin count be handled in the options?

        this.update_color_gradient();
        this.update_axes_alignment();
		this.update_axes_flipping();
		this.update_axes_visibility();
    }
}
