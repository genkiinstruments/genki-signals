import { BasePlot, get_default_plot_options } from './baseplot';
import type { PlotOptions } from './baseplot';

import {
	EAutoRange,
	FastLineRenderableSeries,
	NumberRange,
	NumericAxis,
	SciChartSubSurface,
	SciChartSurface,
	XyDataSeries
} from 'scichart';
import type { TSciChart, NumberArray } from 'scichart';

export interface TracePlotOptions extends PlotOptions {
	type: 'trace';
	/** If auto_range_x is true, then x_domain_max and x_domain_min are not used */
	auto_range_x: boolean;
	/** If auto_range_y is true, then y_domain_max and y_domain_min are not used */
	auto_range_y: boolean;
	x_domain_max: number;
	x_domain_min: number;
	y_domain_max: number;
	y_domain_min: number;
	buffer_size: number;
}
export const default_trace_plot_options: TracePlotOptions = {
	...get_default_plot_options(),
	auto_range_x: false,
	auto_range_y: false,
	x_domain_max: 2560,
	x_domain_min: 0,
	y_domain_max: 1440,
	y_domain_min: 0,
	buffer_size: 1000,
	type: 'trace'
};

export class Trace extends BasePlot {
	renderable_series: FastLineRenderableSeries;
	x_axis: NumericAxis;
	y_axis: NumericAxis;
	data_series: XyDataSeries;
	options: TracePlotOptions;

	constructor(
		wasm_context: TSciChart,
		surface: SciChartSubSurface | SciChartSurface,
		plot_options: TracePlotOptions = default_trace_plot_options
	) {
		super(wasm_context, surface);

		this.renderable_series = new FastLineRenderableSeries(this.wasm_context);
		this.x_axis = new NumericAxis(this.wasm_context);
		this.y_axis = new NumericAxis(this.wasm_context);
		this.data_series = new XyDataSeries(this.wasm_context);
		this.options = plot_options;

		this.surface.xAxes.add(this.x_axis);
		this.surface.yAxes.add(this.y_axis);
		this.renderable_series.dataSeries = this.data_series;
	}

	private update_axis_domains(): void {
		if (this.options.auto_range) {
			this.y_axis.autoRange = EAutoRange.Always;
		} else {
			this.y_axis.autoRange = EAutoRange.Never;
			this.y_axis.visibleRange = new NumberRange(
				this.options.y_domain_min,
				this.options.y_domain_max
			);
		}

		const x_max = this._get_native_x(-1);
		const x_min = this._get_native_x(-this.options.n_visible_points);

		this.x_axis.visibleRange = new NumberRange(x_min, x_max);
	}

	public set_axis_domains(
		auto_range: boolean,
		y_max: number,
		y_min: number,
		n_visible_points: number
	): void {
		this.options.auto_range = auto_range;
		this.options.y_domain_max = y_max;
		this.options.y_domain_min = y_min;
		this.options.n_visible_points = n_visible_points;
		this.update_axis_domains();
	}

	public update(x: NumberArray, y: NumberArray): void {
		this.data_series.appendRange(x, y);
		this.update_axis_domains();
	}
}
