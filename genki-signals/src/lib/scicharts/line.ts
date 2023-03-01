import {
	EAutoRange,
	FastLineRenderableSeries,
	NumberRange,
	NumericAxis,
	SciChartSubSurface,
	SciChartSurface,
	XyDataSeries,
	type TSciChart
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
		auto_range: false,
		y_domain_max: 1,
		y_domain_min: 0,
		n_visible_points: 100,
		type: 'line' // overrides default_plot_options.type
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

		this.options.sig_y.forEach(() => this.append_line()); // one to one mapping of data series to renderable series

		this.update_axes_alignment();
		this.update_axes_flipping();
		this.update_axes_visibility();
	}

	private append_line(): void {
		const renderable_series = new FastLineRenderableSeries(this.wasm_context);
		const data_series = new XyDataSeries(this.wasm_context);
		data_series.containsNaN = this.options.data_contains_nan;
		data_series.isSorted = this.options.data_is_sorted;
		renderable_series.dataSeries = data_series;

		this.surface.renderableSeries.add(renderable_series);
		this.renderable_series.push(renderable_series);
		this.data_series.push(data_series);
	}

	public add_line(sig_y: SignalConfig) {
		this.options.sig_y.push(sig_y);
		this.append_line();
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

	public update(data: ArrayDict): void {
		const x = this.fetch_and_check(data, this.options.sig_x);

		this.options.sig_y.forEach((sig_y, i) => {
			const y = this.fetch_and_check(data, sig_y);
			this.data_series[i].appendRange(x, y);
		});

		this.update_axis_domains();
	}
}
