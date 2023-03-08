import {
	FastColumnRenderableSeries,
    EAutoRange,
	NumberRange,
	NumericAxis,
    CategoryAxis,
	SciChartSubSurface,
	SciChartSurface,
	XyDataSeries,
	MouseWheelZoomModifier,
	ZoomExtentsModifier,
	ZoomPanModifier,
	EZoomState,
    EHorizontalTextPosition,
    EVerticalTextPosition,
    TextLabelProvider,
    Thickness,
	type TSciChart
} from 'scichart';

import { BasePlot, get_default_plot_options, type PlotOptions } from './baseplot';
import { compare_signals } from './types';
import type { ArrayDict, SignalConfig } from './types';

export interface BarPlotOptions extends PlotOptions {
	type: 'bar';
    /** If auto range is true, then y_domain_max and y_domain_min are not used */
	auto_range: boolean;
	y_domain_max: number;
	y_domain_min: number;
}
export function get_default_bar_plot_options(): BarPlotOptions {
	return {
		...get_default_plot_options(),
		type: 'bar', // overrides default_plot_options.type
        auto_range: true,
		y_domain_max: 1,
		y_domain_min: 0,
	};
}

export class Bar extends BasePlot {
	x_axis: NumericAxis;
	y_axis: NumericAxis;
	options: BarPlotOptions;

	renderable_series: FastColumnRenderableSeries[] = [];
	data_series: XyDataSeries[] = [];

	constructor(
		wasm_context: TSciChart,
		surface: SciChartSubSurface | SciChartSurface,
		plot_options: BarPlotOptions = get_default_bar_plot_options()
	) {
		super(wasm_context, surface);

		this.x_axis = new NumericAxis(this.wasm_context, {autoRange: EAutoRange.Always});
		this.y_axis = new NumericAxis(this.wasm_context, {growBy: new NumberRange(0,0.2)});
		this.surface.xAxes.add(this.x_axis);
		this.surface.yAxes.add(this.y_axis);

		this.options = plot_options;

		if (this.options.sig_x.length != 0) {
			throw new Error('Bar plot does not support x signals');
		}

		this.create_plot();

		this.update_y_domain();
		this.update_axes_alignment();
		this.update_axes_flipping();
		this.update_axes_visibility();
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
        this.data_series[0]?.clear()
		this.options.sig_y.forEach((sig_y, i) => {
			const y = this.fetch_and_check(data, sig_y);
			this.data_series[0]?.append(i, y[y.length-1]);
		});
	}

    private update_label_format(){
        this.x_axis.labelProvider = new TextLabelProvider({
            labels: this.options.sig_y.map((sig_config) => sig_config.sig_name + "_" + sig_config.sig_idx)
        });
    }

	private create_plot(): void {
		const renderable_series = new FastColumnRenderableSeries(this.wasm_context, {
            dataLabels: {
                horizontalTextPosition: EHorizontalTextPosition.Center,
                verticalTextPosition: EVerticalTextPosition.Above,
                style: { fontFamily: "Arial", fontSize: 16, padding: new Thickness(0,0,20,0) },
                color: "#FFFFFF",
            },
        });
		const data_series = new XyDataSeries(this.wasm_context);
		data_series.containsNaN = this.options.data_contains_nan;
		data_series.isSorted = this.options.data_is_sorted;
		renderable_series.dataSeries = data_series;

		this.surface.renderableSeries.add(renderable_series);
		this.renderable_series.push(renderable_series);
		this.data_series.push(data_series);

        this.update_label_format();
	}

	public add_plot(sig_y: SignalConfig, sig_x: SignalConfig | null = null): void {
		if (sig_x !== null) {
			throw new Error(
				'x signal is not supported for bar plots'
			);
		}

		this.options.sig_y.forEach((sig) => {
			if (compare_signals(sig, sig_y)) {
				throw new Error('Signal already exists in plot');
			}
		});

		this.options.sig_y.push(sig_y);

        this.update_label_format();
	}

	public remove_plot(sig_y: SignalConfig, sig_x: SignalConfig | null = null) {
		if (sig_x !== null) {
			throw new Error(
				'x signal is not supported for bar plots'
			);
		}

		let deleted = false;

		this.options.sig_y.forEach((sig, idx) => {
			if (compare_signals(sig, sig_y)) {
				this.options.sig_y.splice(idx, 1);
				deleted = true;
			}
		});

		if (!deleted) {
			throw new Error('Signal does not exist on this plot');
		}

        this.update_label_format();
	}

	public update_all_options(options: BarPlotOptions): void {
		this.options = options

		this.update_y_domain();
		this.update_axes_alignment();
		this.update_axes_flipping();
		this.update_axes_visibility();
		this.update_axes_visibility();
		this.update_data_optimizations();
	}
}
