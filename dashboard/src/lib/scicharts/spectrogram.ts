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
import type { ArrayDict, SignalConfig } from './types';

export interface SpectrogramPlotOptions extends PlotOptions {
	type: 'spectrogram';
    window_size: number;
    sampling_rate: number;
	n_visible_windows: number;
    colormap_min: number;
    colormap_max: number;
}
export function get_default_spectrogram_plot_options(): SpectrogramPlotOptions {
	return {
		...get_default_plot_options(),
		type: 'spectrogram', // overrides default_plot_options.type
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

    zValues: number[][];

	renderable_series: UniformHeatmapRenderableSeries[] = [];
	data_series: UniformHeatmapDataSeries[] = [];

	constructor(
		wasm_context: TSciChart,
		surface: SciChartSubSurface | SciChartSurface,
		plot_options: SpectrogramPlotOptions = get_default_spectrogram_plot_options()
	) {
		super(wasm_context, surface);

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

		if (this.options.sig_y.length > 1 ) {
			throw new Error('Spectrogram only support one y signal');
		}
        if (this.options.sig_x.length > 0 ) {
			throw new Error('Spectrogram does not support x signals');
		}

        this.surface.chartModifiers.add(new MouseWheelZoomModifier());
        this.surface.chartModifiers.add(new ZoomPanModifier());
        this.surface.chartModifiers.add(new ZoomExtentsModifier());

		this.create_plot();

		this.update_axes_alignment();
		this.update_axes_flipping();
		this.update_axes_visibility();
	}

	public update(data: ArrayDict): void {
		if (this.options.sig_y.length !== 1) return; // if no x signal is defined, then we can't update the plot

        const sig_name = this.options.sig_y[0].sig_name;
		if (!(sig_name in data)) throw new Error(`sig_name ${sig_name} not in data`);

        if(data[sig_name][0].length == 0) return; // no new data

        this.zValues = this.zValues.map((row, i) => row.concat(data[sig_name][i]).slice(-this.options.n_visible_windows))

        this.data_series[0].setZValues(this.zValues);
	}

	private create_plot(): void {
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
        const bin_count = Math.floor(this.options.window_size/2) + 1;
        this.zValues = zeroArray2D([bin_count, this.options.n_visible_windows])
		const data_series = new UniformHeatmapDataSeries(this.wasm_context, {
            xStart: 0,
            xStep: 1,
            yStart: 0,
            yStep: this.options.sampling_rate/this.options.window_size,
            zValues: this.zValues
        });

		renderable_series.dataSeries = data_series;

		this.surface.renderableSeries.add(renderable_series);
		this.renderable_series.push(renderable_series);
		this.data_series.push(data_series);

        this.x_axis.visibleRange = new NumberRange(0, this.options.n_visible_windows);
        this.y_axis.visibleRange = new NumberRange(0, (bin_count-1) * this.options.sampling_rate/this.options.window_size);
        this.x_axis.visibleRangeLimit = this.x_axis.visibleRange;
        this.y_axis.visibleRangeLimit = this.y_axis.visibleRange;
	}

	public add_plot(sig_y: SignalConfig, sig_x: SignalConfig | null = null): void {
        throw new Error(
            'This method is not supported for Spectrogram'
        );
	}

	public remove_plot(sig_y: SignalConfig, sig_x: SignalConfig | null = null) {
        throw new Error(
            'This method is not supported for Spectrogram'
        );
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
        const new_window_size = options.window_size != this.window_size;
        const new_sampling_rate = options.sampling_rate != this.sampling_rate;
        const new_n_visible_windows = options.n_visible_windows != this.zValues[0]?.length;
        this.options = options;
        if(new_window_size || new_n_visible_windows || new_sampling_rate){
            this.window_size = this.options.window_size;
            this.sampling_rate = this.options.sampling_rate;
            this.create_plot();
        }
        this.update_color_gradient();
        this.update_axes_alignment();
		this.update_axes_flipping();
		this.update_axes_visibility();
    }
}
