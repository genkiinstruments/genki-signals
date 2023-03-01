import { EAxisAlignment, type NumberArray } from 'scichart';
import type { TSciChart, AxisBase2D, BaseRenderableSeries, SciChartSubSurface, SciChartSurface, BaseDataSeries } from 'scichart';

import type { Deletable, Updatable } from './interfaces';
import type {  SignalConfig, ArrayDict } from './types';

export interface PlotOptions {
    type: string,
	x_axis_align: 'top' | 'bottom';
	y_axis_align: 'left' | 'right';
	x_axis_flipped: boolean;
	y_axis_flipped: boolean;
	x_axis_visible: boolean; // TODO: implement
	y_axis_visible: boolean;
	data_contains_nan: boolean;
	data_is_sorted: boolean;
    sig_x: SignalConfig;
    sig_y: SignalConfig[];  // This defines the signals that are plotted
}
export function get_default_plot_options(): PlotOptions { // Function so that a copy is returned
    return {
        type: 'no_type',
        x_axis_align: 'bottom',
        y_axis_align: 'left',
        x_axis_flipped: false,
        y_axis_flipped: false,
        x_axis_visible: true,
        y_axis_visible: true,
        data_contains_nan: false,
        data_is_sorted: false,
        sig_x: { sig_name: 'timestamp_us', sig_idx: 0 },
        sig_y: [],
    };
} 


export abstract class BasePlot implements Updatable, Deletable {
	protected wasm_context: TSciChart;
	protected surface: SciChartSubSurface | SciChartSurface;
	
    protected abstract options: PlotOptions;

	protected abstract x_axis: AxisBase2D;
	protected abstract y_axis: AxisBase2D;
	protected abstract renderable_series: BaseRenderableSeries[];
	protected abstract data_series: BaseDataSeries[];


	constructor(wasm_context: TSciChart, surface: SciChartSubSurface | SciChartSurface) {
		this.wasm_context = wasm_context;
		this.surface = surface;
	}

	/**
	 * @param i - The index of the data series. If i is negative, then the index is counted from the end.
	 * @returns The x-value at index i.
	 */
	protected _get_native_x(i: number): number {
        const data_series = this.data_series[0]; // All series have the same x-values
        const count = data_series.count();
		const x_values = data_series.getNativeXValues();

		if (i < 0) {
			return x_values.get(Math.max(count + i, 0));
		}
		return x_values.get(i);
	}

	protected update_axes_alignment(): void {
		switch (this.options.x_axis_align) {
			case 'top':
				this.x_axis.axisAlignment = EAxisAlignment.Top;
				break;
			case 'bottom':
				this.x_axis.axisAlignment = EAxisAlignment.Bottom;
				break;
			default:
				throw new Error(`Invalid x-axis alignment: ${this.options.x_axis_align}`);
		}
		switch (this.options.y_axis_align) {
			case 'left':
				this.y_axis.axisAlignment = EAxisAlignment.Left;
				break;
			case 'right':
				this.y_axis.axisAlignment = EAxisAlignment.Right;
				break;
			default:
				throw new Error(`Invalid y-axis alignment: ${this.options.y_axis_align}`);
		}
	}

	protected update_axes_flipping(): void {
		this.x_axis.flippedCoordinates = this.options.x_axis_flipped;
		this.y_axis.flippedCoordinates = this.options.y_axis_flipped;
	}

    protected update_axes_visibility(): void {
        this.x_axis.isVisible = this.options.x_axis_visible;
        this.y_axis.isVisible = this.options.y_axis_visible;
    }

	// TODO: abstract set_options instead?
	public set_axis_alignment(x_align: 'top' | 'bottom', y_align: 'left' | 'right'): void {
		this.options.x_axis_align = x_align;
		this.options.y_axis_align = y_align;
		this.update_axes_alignment();
	}

	public set_axis_flipped(x_axis_flipped: boolean, y_axis_flipped: boolean): void {
		this.options.x_axis_flipped = x_axis_flipped;
		this.options.y_axis_flipped = y_axis_flipped;
		this.update_axes_flipping();
	}

    /**
     * Access the data with the given signal config and throws errors.
     * @param data - The data to access
     * @param sig - The signal config to access
     * @returns the data at signal_config.name and signal_config.idx
     */
    protected fetch_and_check(data: ArrayDict, sig: SignalConfig): NumberArray {
		const sig_name = sig.sig_name;
		const sig_idx = sig.sig_idx;
		if (!(sig_name in data)) throw new Error(`sig_name ${sig_name} not in data`);
		if (sig_idx >= data[sig_name].length) throw new Error(`sig_idx ${sig_idx} out of bounds`);

		return data[sig_name][sig_idx] as NumberArray;
	}

	public abstract update(data: ArrayDict): void;

	public delete(): void {
		this.surface.xAxes.remove(this.x_axis);
		this.surface.yAxes.remove(this.y_axis);
		this.x_axis.delete();
		this.y_axis.delete();
        this.surface.delete();

        this.renderable_series.forEach((rs) => rs.delete());
		this.data_series.forEach((ds) => ds.delete());
	}

	// TODO: abstract method to set options
	// public abstract set_options(options: PlotOptions): void;
}
