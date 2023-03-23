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
import { Signal, type ISignalConfig } from './signal';
import type { IArrayDict } from './interfaces';

export interface LinePlotOptions extends PlotOptions {
	/** If auto range is true, then y_domain_max and y_domain_min are not used */
	auto_range: boolean;
	y_domain_max: number;
	y_domain_min: number;
	n_visible_points: number;
}
export function get_default_line_plot_options(): LinePlotOptions {
	return {
		...get_default_plot_options(),
		name: 'Line',
		auto_range: true,
		y_domain_max: 1,
		y_domain_min: 0,
		n_visible_points: 1000
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
		surface: SciChartSubSurface,
		plot_options: LinePlotOptions = get_default_line_plot_options(),
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


	public update(data: IArrayDict): void {
		const x = this.check_and_fetch(data, this.sig_x);

		this.sig_y.forEach((sig, i) => {
			const y = this.check_and_fetch(data, sig);
			this.data_series[i].appendRange(x, y);
		});

		if (this.sig_y.length === 0 || this.surface.zoomState == EZoomState.UserZooming) return;

		this.update_x_domain();
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


	public update_all_options(options: LinePlotOptions): void {
		this.options = options;
		
		this.update_x_domain();
		this.update_y_domain();
		this.update_axes_alignment();
		this.update_axes_flipping();
		this.update_axes_visibility();
		this.update_data_optimizations();
	}
}
