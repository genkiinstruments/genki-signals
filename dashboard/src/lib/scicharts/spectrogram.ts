import {
	EAutoRange,
	NumberRange,
	NumericAxis,
	SciChartSubSurface,
	SciChartSurface,
    UniformHeatmapDataSeries,
    UniformHeatmapRenderableSeries,
	EZoomState,
	type TSciChart
} from 'scichart';

import { BasePlot, get_default_plot_options, type PlotOptions } from './baseplot';
import { compare_signals } from './types';
import type { ArrayDict, SignalConfig } from './types';

export interface SpectrogramPlotOptions extends PlotOptions {
	type: 'spectrogram';
	/** If auto range is true, then y_domain_max and y_domain_min are not used */
	n_visible_windows: number;
}
export function get_default_spectogram_plot_options(): SpectrogramPlotOptions {
	return {
		...get_default_plot_options(),
		type: 'spectrogram', // overrides default_plot_options.type
		n_visible_windows: 1
	};
}

export class Spectrogram extends BasePlot {
	x_axis: NumericAxis;
	y_axis: NumericAxis;
	options: SpectrogramPlotOptions;

	renderable_series: UniformHeatmapRenderableSeries[] = [];
	data_series: UniformHeatmapDataSeries[] = [];

	constructor(
		wasm_context: TSciChart,
		surface: SciChartSubSurface | SciChartSurface,
		plot_options: SpectrogramPlotOptions = get_default_spectogram_plot_options()
	) {
		super(wasm_context, surface);

		this.x_axis = new NumericAxis(this.wasm_context, {
            autoRange: EAutoRange.Always,
            drawLabels: false,
            drawMinorTickLines: false,
            drawMajorTickLines: false
        });
		this.y_axis = new NumericAxis(this.wasm_context, {
            autoRange: EAutoRange.Always,
            drawLabels: false,
            drawMinorTickLines: false,
            drawMajorTickLines: false
        });

		this.surface.xAxes.add(this.x_axis);
		this.surface.yAxes.add(this.y_axis);

		this.options = plot_options;

		if (this.options.sig_x.length > 1) {
			throw new Error('Line plots only support one x signal');
		}

		// sig_y implicitly defines the number of plots
		this.options.sig_y.forEach(() => this.create_plot()); // one to one mapping of data series to renderable series

		this.update_y_domain();
		this.update_axes_alignment();
		this.update_axes_flipping();
		this.update_axes_visibility();
	}

	private update_x_domain(): void {
		const x_max = this.get_native_x(-1);
		const x_min = this.get_native_x(-this.options.n_visible_points);
		this.x_axis.visibleRange = new NumberRange(x_min, x_max);
	}

	public set_axis_domains(
		auto_range: boolean,
		y_max: number,
		y_min: number,
		n_visible_points: number
	): void {
		// this.options.auto_range = auto_range;
		// this.options.y_domain_max = y_max;
		// this.options.y_domain_min = y_min;
		// this.options.n_visible_points = n_visible_points;
		// this.update_x_domain();
	}

	public update(data: ArrayDict): void {
		if (this.options.sig_x.length === 0) return; // if no x signal is defined, then we can't update the plot

		const x = this.fetch_and_check(data, this.options.sig_x[0]);

		this.options.sig_y.forEach((sig_y, i) => {
			const y = this.fetch_and_check(data, sig_y);
			this.data_series[i].appendRange(x, y);
		});

		if (this.options.sig_y.length === 0 || this.surface.zoomState == EZoomState.UserZooming) return;

		this.update_x_domain();
	}

	private create_plot(): void {
		const renderable_series = new UniformHeatmapRenderableSeries(this.wasm_context);
		const data_series = new UniformHeatmapDataSeries(this.wasm_context, {
            xStart: 0,
            xStep: 1,
            yStart: 0,
            yStep: 1,
        });

		data_series.containsNaN = this.options.data_contains_nan;
		data_series.isSorted = this.options.data_is_sorted;
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
}
