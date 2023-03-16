import {
	EAutoRange,
	FastLineRenderableSeries,
	NumberRange,
	NumericAxis,
	SciChartSubSurface,
	SciChartSurface,
	XyDataSeries,
	MouseWheelZoomModifier,
	ZoomExtentsModifier,
	ZoomPanModifier,
	EZoomState,
	type TSciChart,
} from 'scichart';

import { BasePlot, get_default_plot_options, type PlotOptions } from './baseplot';
import type { ArrayDict, SignalConfig } from './types';

export interface LinePlotOptions extends PlotOptions {
	type: 'line';
	/** If auto range is true, then y_domain_max and y_domain_min are not used */
	auto_range: boolean;
	y_domain_max: number;
	y_domain_min: number;
	n_visible_points: number;
}
export function get_default_line_plot_options(): LinePlotOptions {
	return {
		...get_default_plot_options(),
		type: 'line', // overrides default_plot_options.type
		auto_range: true,
		y_domain_max: 1,
		y_domain_min: 0,
		n_visible_points: 10000
	};
}

export class Line extends BasePlot {
	x_axis: NumericAxis;
	y_axis: NumericAxis;
	options: LinePlotOptions;

	renderable_series: FastLineRenderableSeries[] = [];
	data_series: XyDataSeries[] = [];

	constructor(
		wasm_context: TSciChart,
		surface: SciChartSubSurface | SciChartSurface,
		plot_options: LinePlotOptions = get_default_line_plot_options()
	) {
		super(wasm_context, surface);

		this.x_axis = new NumericAxis(this.wasm_context);
		this.y_axis = new NumericAxis(this.wasm_context);
		this.surface.xAxes.add(this.x_axis);
		this.surface.yAxes.add(this.y_axis);

		this.options = plot_options;

		// sig_y implicitly defines the number of plots
		this.options.sig_y.forEach(() => this.add_plot()); // one to one mapping of data series to renderable series

		this.surface.chartModifiers.add(new MouseWheelZoomModifier());
        this.surface.chartModifiers.add(new ZoomPanModifier());
        this.surface.chartModifiers.add(new ZoomExtentsModifier({isAnimated: false}));

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


	private update_y_domain(): void {
		if (this.options.auto_range) {
			this.y_axis.autoRange = EAutoRange.Always;
		} else {
			this.y_axis.autoRange = EAutoRange.Never;
			this.y_axis.visibleRange = new NumberRange(
				this.options.y_domain_min,
				this.options.y_domain_max
			);
		}
	}


	public update(data: ArrayDict): void {
		if (this.options.sig_x.length === 0) return; // if no x signal is defined, then we can't update the plot
		
		const x = this.check_and_fetch(data, this.options.sig_x[0]);

		this.options.sig_y.forEach((sig_y, i) => {
			const y = this.check_and_fetch(data, sig_y);
			this.data_series[i].appendRange(x, y);
		});

		if (this.options.sig_y.length === 0 || this.surface.zoomState == EZoomState.UserZooming) return;

		this.update_x_domain();
	}

	private add_plot(): void {
		const data_series = new XyDataSeries(this.wasm_context);
		data_series.isSorted = this.options.data_is_sorted;
		data_series.containsNaN = this.options.data_contains_nan;

		const renderable_series = new FastLineRenderableSeries(this.wasm_context);
		renderable_series.dataSeries = data_series;

		this.surface.renderableSeries.add(renderable_series);
		this.renderable_series.push(renderable_series);
		this.data_series.push(data_series);
	}


	public update_all_options(options: LinePlotOptions): void {
		console.log('new options', options);
		console.log('old options', this.options);
		// These function check for changes and execute appropriately
		this.update_sig_x(options.sig_x);
		this.update_sig_y(options.sig_y);

		this.options = options;
		
		this.update_x_domain();
		this.update_y_domain();
		this.update_axes_alignment();
		this.update_axes_flipping();
		this.update_axes_visibility();
		this.update_data_optimizations();
	}
}
