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
	type TSciChart
} from 'scichart';

import { BasePlot, get_default_plot_options, type PlotOptions } from './baseplot';
import type { IArrayDict } from './interfaces';
import type { ISignalConfig } from './signal';

export interface TracePlotOptions extends PlotOptions {
	/** If auto_range_x is true, then x_domain_max and x_domain_min are not used */
	auto_range_x: boolean;
	/** If auto_range_y is true, then y_domain_max and y_domain_min are not used */
	auto_range_y: boolean;
	x_domain_max: number;
	x_domain_min: number;
	y_domain_max: number;
	y_domain_min: number;
	n_visible_points: number;
}
export function get_default_trace_plot_options(): TracePlotOptions {
    return {
        ...get_default_plot_options(),
		name: 'Trace',
		data_is_sorted: false, // overrides default_plot_options.data_is_sorted
        auto_range_x: false,
        auto_range_y: false,
        x_domain_max: 2560,
        x_domain_min: 0,
        y_domain_max: 1440,
        y_domain_min: 0,
        n_visible_points: 100
    };
} 


export class Trace extends BasePlot {
	x_axis: NumericAxis;
	y_axis: NumericAxis;
	options: TracePlotOptions;

	renderable_series: FastLineRenderableSeries[] = [];
	data_series: XyDataSeries[] = [];

	constructor(
		wasm_context: TSciChart,
		surface: SciChartSubSurface,
		plot_options: TracePlotOptions = get_default_trace_plot_options(),
		sig_x_config: ISignalConfig = { key: '', idx: 0 },
		sig_y_config: ISignalConfig[] = []
	) {
		super(wasm_context, surface, sig_x_config, sig_y_config);

		this.x_axis = new NumericAxis(this.wasm_context);
		this.y_axis = new NumericAxis(this.wasm_context);
		this.surface.xAxes.add(this.x_axis);
		this.surface.yAxes.add(this.y_axis);

		this.options = plot_options;

		this.surface.chartModifiers.add(new MouseWheelZoomModifier());
        this.surface.chartModifiers.add(new ZoomPanModifier());
        this.surface.chartModifiers.add(new ZoomExtentsModifier({onZoomExtents: () => {
			if(!this.options.auto_range_x){
				this.x_axis.visibleRange = new NumberRange(this.options.x_domain_min, this.options.x_domain_max);
			}
			if(!this.options.auto_range_y){
				this.y_axis.visibleRange = new NumberRange(this.options.y_domain_min, this.options.y_domain_max);
			}
			return false
		}}));

		this.update_axes_alignment();
		this.update_axes_flipping();
		this.update_axes_visibility();
		this.update_x_domains();
		this.update_y_domains();
		this.update_data_optimizations();
	}

	private update_x_domains(): void {
		if (this.options.auto_range_x) {
			this.x_axis.autoRange = EAutoRange.Always;
			return;
		} 

		this.x_axis.autoRange = EAutoRange.Never;
		const x_min = this.options.x_domain_min;
		const x_max = this.options.x_domain_max;
		this.x_axis.visibleRange = new NumberRange(x_min, x_max);
	}

	private update_y_domains(): void {
		if (this.options.auto_range_y) {
			this.y_axis.autoRange = EAutoRange.Always;
			return;
		}

		this.y_axis.autoRange = EAutoRange.Never;
		const y_min = this.options.y_domain_min;
		const y_max = this.options.y_domain_max;
		this.y_axis.visibleRange = new NumberRange(y_min, y_max);
	}

	public update(data: IArrayDict): void {
		const x = this.check_and_fetch(data, this.sig_x);

		this.sig_y.forEach((sig, i) => {
			const y = this.check_and_fetch(data, sig);

			const ds = this.data_series[i];
			if (ds === undefined) throw new Error(`Data series at ${i} is undefined`);
			ds.appendRange(x, y);

			if (ds.count() > this.options.n_visible_points) {
				ds.removeRange(0, ds.count() - this.options.n_visible_points);
			}
		});
	}

	protected add_renderable(at: number = -1): void {
		if (at === -1) at = this.renderable_series.length;
		if (at > this.renderable_series.length) return;

		const data_series = new XyDataSeries(this.wasm_context);
		data_series.isSorted = this.options.data_is_sorted;
		data_series.containsNaN = this.options.data_contains_nan;

		const renderable_series = new FastLineRenderableSeries(this.wasm_context);
		renderable_series.dataSeries = data_series;

		this.surface.renderableSeries.add(renderable_series);
		this.renderable_series.splice(at, 0, renderable_series);
		this.data_series.splice(at, 0, data_series);
	}

	public update_all_options(options: TracePlotOptions): void {
		this.options = options;

		this.update_axes_alignment();
		this.update_axes_flipping();
		this.update_axes_visibility();
		this.update_x_domains();
		this.update_y_domains();
	}
}
