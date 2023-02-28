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

import { BasePlot, default_plot_options } from './baseplot';
import type { PlotOptions } from './baseplot';

export interface LinePlotOptions extends PlotOptions {
	/** If auto range is true, then y_domain_max and y_domain_min are not used */
	auto_range: boolean;
	y_domain_max: number;
	y_domain_min: number;
	n_visible_points: number;
	type: 'line'; // TODO: Hack, overrides the no_type default as 'immutable' "line"
}
export const default_line_plot_options: LinePlotOptions = {
	...default_plot_options,
	auto_range: false,
	y_domain_max: 1,
	y_domain_min: 0,
	n_visible_points: 100,
	type: 'line'
};

export class Line extends BasePlot {
	renderable_series: FastLineRenderableSeries;
	x_axis: NumericAxis;
	y_axis: NumericAxis;
	data_series: XyDataSeries;
	options: LinePlotOptions;

	constructor(
		wasm_context: TSciChart,
		surface: SciChartSubSurface | SciChartSurface,
		plot_options: LinePlotOptions = default_line_plot_options
	) {
		super(wasm_context, surface);

		this.renderable_series = new FastLineRenderableSeries(this.wasm_context);
		this.x_axis = new NumericAxis(this.wasm_context);
		this.y_axis = new NumericAxis(this.wasm_context);
		this.data_series = new XyDataSeries(this.wasm_context);
		this.options = plot_options;

		this.data_series.containsNaN = this.options.data_contains_nan;
		this.data_series.isSorted = this.options.data_is_sorted;

		this.surface.xAxes.add(this.x_axis);
		this.surface.yAxes.add(this.y_axis);
		this.renderable_series.dataSeries = this.data_series;

		this.surface.renderableSeries.add(this.renderable_series);

		this.update_axes_alignment();
        this.update_axes_flipping();
        this.update_axes_visibility();
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
