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
} from 'scichart';

import { BasePlot, get_default_plot_options, type PlotOptions } from './baseplot';
import type { ArrayDict, SignalConfig } from './types';

export interface SpectrogramPlotOptions extends PlotOptions {
	type: 'spectrogram';
    bin_count: number;
	n_visible_windows: number;
    colormap_min: number;
    colormap_max: number;
}
export function get_default_spectrogram_plot_options(): SpectrogramPlotOptions {
	return {
		...get_default_plot_options(),
		type: 'spectrogram', // overrides default_plot_options.type
        bin_count: 128,
		n_visible_windows: 1,
        colormap_min: 0,
        colormap_max: 1,
	};
}

export class Spectrogram extends BasePlot {
	x_axis: NumericAxis;
	y_axis: NumericAxis;
	options: SpectrogramPlotOptions;
    n_visible_windows: number;

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
            autoRange: EAutoRange.Always,
            drawLabels: false,
            drawMinorTickLines: false,
            drawMajorTickLines: false,
        });
		this.y_axis = new NumericAxis(this.wasm_context, {
            autoRange: EAutoRange.Always,
            drawLabels: false,
            drawMinorTickLines: false,
            drawMajorTickLines: false,
        });

		this.surface.xAxes.add(this.x_axis);
		this.surface.yAxes.add(this.y_axis);

		this.options = plot_options;
        this.n_visible_windows = this.options.n_visible_windows;

		if (this.options.sig_y.length > 1 ) {
			throw new Error('Spectrogram only support one y signal');
		}
        if (this.options.sig_x.length > 0 ) {
			throw new Error('Spectrogram does not support x signals');
		}

		this.create_plot();

		this.update_axes_alignment();
		this.update_axes_flipping();
		this.update_axes_visibility();
	}

	public update(data: ArrayDict): void {
		if (this.options.sig_y.length !== 1) return; // if no x signal is defined, then we can't update the plot

        const sig_name = this.options.sig_y[0].sig_name;
		if (!(sig_name in data)) throw new Error(`sig_name ${sig_name} not in data`);  
    
        this.zValues = this.zValues.map((row, i) => row.concat(data[sig_name][i]).slice(-this.options.n_visible_windows - 1, -1))

        this.data_series[0].setZValues(this.zValues);
	}

	private create_plot(): void {
		const renderable_series = new UniformHeatmapRenderableSeries(this.wasm_context, {
            colorMap: new HeatmapColorMap({
                minimum: this.options.colormap_min,
                maximum: this.options.colormap_max,
                gradientStops: [
                    {offset: 0, color: "#000000"},
                    {offset: 0.05, color: "#800080"},
                    {offset: 0.2, color: "#FF0000"},
                    {offset: 0.5, color: "#FFFF00"},
                    {offset: 1, color: "#FFFFFF"}
                ]
            }),
            dataLabels: {
                numericFormat: ENumericFormat.NoFormat,
                precision: 10,
            }
        });
        this.zValues = zeroArray2D([this.options.bin_count, this.options.n_visible_windows])
		const data_series = new UniformHeatmapDataSeries(this.wasm_context, {
            xStart: 0,
            xStep: 1,
            yStart: 0,
            yStep: 1,
            zValues: this.zValues
        });

		renderable_series.dataSeries = data_series;

		this.surface.renderableSeries.add(renderable_series);
		this.renderable_series.push(renderable_series);
		this.data_series.push(data_series);
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

    public update_all_options(options: SpectrogramPlotOptions): void {
        let reinit = options.n_visible_windows != this.n_visible_windows;
        this.options = options;
        if(reinit){
            this.data_series[0].delete();
            this.renderable_series[0].delete();
            this.data_series = [];
            this.renderable_series = [];
            this.create_plot()
            this.n_visible_windows = this.options.n_visible_windows;
        }
        this.update_axes_alignment();
		this.update_axes_flipping();
		this.update_axes_visibility();
    }
}
