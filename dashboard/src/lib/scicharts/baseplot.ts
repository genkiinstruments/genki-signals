import { EAxisAlignment, type NumberArray } from 'scichart';
import type {
	TSciChart,
	AxisBase2D,
	BaseRenderableSeries,
	SciChartSubSurface,
	SciChartSurface,
	BaseDataSeries
} from 'scichart';

import type { Deletable, Updatable } from './interfaces';
import type { SignalConfig, ArrayDict } from './types';

export interface PlotOptions {
	type: string;
	description: string;
	/**
	 * Some plots have a 1 to n mapping of sig_x to sig_y and others have a 1 to 1 mapping.
	 * In the former case, sig_x.length is maintained at 1.
	 * In the latter case, sig_x.length === sig_y.length is maintained.
	 */
	sig_x: SignalConfig[];
	sig_y: SignalConfig[];
	x_axis_align: 'top' | 'bottom';
	y_axis_align: 'left' | 'right';
	x_axis_flipped: boolean;
	y_axis_flipped: boolean;
	x_axis_visible: boolean;
	y_axis_visible: boolean;
	data_contains_nan: boolean;
	data_is_sorted: boolean;
}
export function get_default_plot_options(): PlotOptions {
	return {
		type: 'no_type',
		description: 'no_description',
		sig_x: [],
		sig_y: [],
		x_axis_align: 'bottom',
		y_axis_align: 'left',
		x_axis_flipped: false,
		y_axis_flipped: false,
		x_axis_visible: true,
		y_axis_visible: true,
		data_contains_nan: false,
		data_is_sorted: true
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
	protected get_native_x(i: number): number {
		const data_series = this.data_series[0]; // All series have the same x-values

		if (data_series === undefined) throw new Error('Data series is undefined');

		const count = data_series.count();
		const x_values = data_series.getNativeXValues();

		if (i < 0) {
			return x_values.get(Math.max(count + i, 0));
		}
		if (i >= count) {
			throw new Error(`Index ${i} out of bounds`);
		}
		return x_values.get(i);
	}

	private axis_alignment(axis: AxisBase2D, axis_alignment: string): void {
		switch (axis_alignment) {
			case 'top':
				axis.axisAlignment = EAxisAlignment.Top;
				break;
			case 'bottom':
				axis.axisAlignment = EAxisAlignment.Bottom;
				break;
			case 'left':
				axis.axisAlignment = EAxisAlignment.Left;
				break;
			case 'right':
				axis.axisAlignment = EAxisAlignment.Right;
				break;
			default:
				throw new Error(`Invalid axis alignment: ${axis_alignment}`);
		}
	}

	protected update_axes_alignment(): void {
		this.axis_alignment(this.x_axis, this.options.x_axis_align);
		this.axis_alignment(this.y_axis, this.options.y_axis_align);
	}

	protected update_axes_flipping(): void {
		this.x_axis.flippedCoordinates = this.options.x_axis_flipped;
		this.y_axis.flippedCoordinates = this.options.y_axis_flipped;
	}

	protected update_axes_visibility(): void {
		this.x_axis.isVisible = this.options.x_axis_visible;
		this.y_axis.isVisible = this.options.y_axis_visible;
	}

	protected update_data_optimizations(): void {
		this.data_series.forEach((ds) => {
			ds.containsNaN = this.options.data_contains_nan;
			ds.isSorted = this.options.data_is_sorted;
		});
	}

	/**
	 * Access the data with the given signal config and throws errors.
	 * @param data - The data to access
	 * @param sig - The signal config to access
	 * @returns data[sig.sig_key][sig.sig_idx]
	 */
	protected fetch_and_check(data: ArrayDict, sig: SignalConfig): NumberArray {
		const sig_key = sig.sig_key;
		const sig_idx = sig.sig_idx;
		if (!(sig_key in data)) return []; //throw new Error(`sig_key ${sig_key} not in data`);
		if (sig_idx >= data[sig_key].length) return []; //throw new Error(`sig_idx ${sig_idx} out of bounds`);

		return data[sig_key][sig_idx] as NumberArray;
	}

	public delete(): void {
		this.surface.xAxes.remove(this.x_axis);
		this.surface.yAxes.remove(this.y_axis);
		this.x_axis.delete();
		this.y_axis.delete();
		this.surface.delete();

		this.renderable_series.forEach((rs) => rs.delete());
		this.data_series.forEach((ds) => ds.delete());
	}

	public abstract update(data: ArrayDict): void;

	/**
     * Creates a new renderable series / data series and adds it to the plot if it does not exist yet.

     * The x component for each plot is predefined and cannot be changed.
     * @param sig_y - The y component signal config to add
     * @param sig_x - The x component signal config to add. Can be null.
     */
	public abstract add_plot(sig_y: SignalConfig, sig_x: SignalConfig | null): void;

	/**
     * Removes a renderable series / data series from the plot if it exists.

     * The x component for each plot is predefined and cannot be changed.
     * @param sig_y - The y component signal config to remove
     * @param sig_x - The x component signal config to remove. Can be null.
     */
	public abstract remove_plot(sig_y: SignalConfig, sig_x: SignalConfig | null): void;


	/**
	 * Calls each update option functions.
	 * @param options - The new plot options
	 */
	public abstract update_all_options(options: PlotOptions): void;
}
