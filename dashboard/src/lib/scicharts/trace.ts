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
import { compare_signals } from './types';
import type { ArrayDict, SignalConfig } from './types';

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
	n_visible_points: number;
}
export function get_default_trace_plot_options(): TracePlotOptions {
    return {
        ...get_default_plot_options(),
        type: 'trace', // overrides default_plot_options.type
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
		surface: SciChartSubSurface | SciChartSurface,
		plot_options: TracePlotOptions = get_default_trace_plot_options()
	) {
		super(wasm_context, surface);

		this.x_axis = new NumericAxis(this.wasm_context);
		this.y_axis = new NumericAxis(this.wasm_context);
		this.surface.xAxes.add(this.x_axis);
		this.surface.yAxes.add(this.y_axis);

		this.options = plot_options;

        if (this.options.sig_x.length !== this.options.sig_y.length) {
            throw new Error('sig_x and sig_y must have the same length');
        }

		this.options.sig_y.forEach(() => this.create_plot()); // one to one mapping of data series to renderable series

		this.update_axes_alignment();
		this.update_axes_flipping();
		this.update_axes_visibility();
	}

	private update_axis_domains(): void {
		if (this.options.auto_range_x) {
			this.x_axis.autoRange = EAutoRange.Always;
		} else {
			this.x_axis.autoRange = EAutoRange.Never;
            const x_min = this.options.x_domain_min;
            const x_max = this.options.x_domain_max;
            this.x_axis.visibleRange = new NumberRange(x_min, x_max);
		}

        if (this.options.auto_range_y) {
            this.y_axis.autoRange = EAutoRange.Always;
        } else {
            this.y_axis.autoRange = EAutoRange.Never;
            const y_min = this.options.y_domain_min;
            const y_max = this.options.y_domain_max;
            this.y_axis.visibleRange = new NumberRange(y_min, y_max);
        }
	}

	public set_axis_domains(
		auto_range_x: boolean, auto_range_y: boolean,y_max: number,y_min: number
    ): void {
		this.options.auto_range_x = auto_range_x;
        this.options.auto_range_y = auto_range_y;
		this.options.y_domain_max = y_max;
		this.options.y_domain_min = y_min;

		this.update_axis_domains();
	}

	public update(data: ArrayDict): void {
        const n = this.options.sig_x.length; // we maintain sig_x and sig_y so that they have the same length

        for (let i = 0; i < n; i++) {
            const x = this.fetch_and_check(data, this.options.sig_x[i]);
            const y = this.fetch_and_check(data, this.options.sig_y[i]);
            this.data_series[i].appendRange(x, y);

			if (this.data_series[i].count() > this.options.n_visible_points) {
				this.data_series[i].removeRange(0, this.data_series[i].count() - this.options.n_visible_points);
			}
        }



		this.update_axis_domains();
	}

	private create_plot(): void {
		const renderable_series = new FastLineRenderableSeries(this.wasm_context);
		const data_series = new XyDataSeries(this.wasm_context);
		data_series.containsNaN = this.options.data_contains_nan;
		data_series.isSorted = this.options.data_is_sorted;
		renderable_series.dataSeries = data_series;
		
		this.surface.renderableSeries.add(renderable_series);
		this.renderable_series.push(renderable_series);
		this.data_series.push(data_series);
	}

	public add_plot(sig_y: SignalConfig) {
		this.options.sig_y.forEach((sig) => {
			if (compare_signals(sig, sig_y)) {
				throw new Error('Signal already exists in plot');
			}
		});

		this.create_plot();
		this.options.sig_y.push(sig_y);		
	}

	public remove_plot(idx: number) {
		if (idx >= this.options.sig_y.length || idx < 0) {
			throw new Error('Index out of bounds');
		}

		this.options.sig_y.splice(idx, 1);
		this.surface.renderableSeries.remove(this.renderable_series[idx]);
		this.renderable_series.splice(idx, 1);
		this.data_series.splice(idx, 1);
	}
}
