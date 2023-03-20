import { BaseHeatmapDataSeries, EAxisAlignment, type NumberArray } from 'scichart';
import type {
	TSciChart,
	AxisBase2D,
	BaseRenderableSeries,
	SciChartSubSurface,
	SciChartSurface,
	BaseDataSeries
} from 'scichart';

import { SignalConfig, type ArrayDict } from './types';
import type { IDeletable, IUpdatable } from './interfaces';

export interface PlotOptions {
	type: string;
	description: string;
	/**
	 * Some plots have a 1 to n mapping of sig_x to sig_y and others have a 1 to 1 mapping.
	 * In the former case, sig_x.length is maintained at 1.
	 * In the latter case, sig_x.length === sig_y.length is maintained.
	 */
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

export abstract class BasePlot implements IUpdatable, IDeletable {
	public readonly wasm_context: TSciChart;
	public readonly surface: SciChartSubSurface;

	protected abstract options: PlotOptions;

	protected abstract x_axis: AxisBase2D;
	protected abstract y_axis: AxisBase2D;

	protected abstract sig_x: SignalConfig;

	// These lists should have the same length
	protected abstract sig_y: SignalConfig[];
	protected abstract renderable_series: BaseRenderableSeries[];
	protected abstract data_series: BaseDataSeries[] | BaseHeatmapDataSeries[];

	constructor(wasm_context: TSciChart, surface: SciChartSubSurface) {
		this.wasm_context = wasm_context;
		this.surface = surface;
	}

	/**
	 * @param at - The index of the data series. If at is negative, then the index is counted from the end.
	 * @returns The x-value at index at.
	 */
	protected get_native_x(at: number): number {
		const data_series = this.data_series[0]; // All series have the same x-values

		if (data_series === undefined) throw new Error('Data series is undefined');

		const count = data_series.count();
		const x_values = data_series.getNativeXValues();

		if (at < 0) {
			return x_values.get(Math.max(count + at, 0));
		}
		if (at >= count) {
			throw new Error(`Index ${at} out of bounds`);
		}
		return x_values.get(at);
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
	 * Updates the signal config for the x-axis. If the new signal config is different from the old one,
	 * then all data series are cleared.
	 * @param sig_x - The new signal config for the x-axis.
	 */
	protected change_sig_x(sig_x: SignalConfig): void {
		console.log('sig_x', sig_x.hasOwnProperty('compare_to'));
		if (!(sig_x.compare_to(this.options.sig_x))) {
			this.data_series.forEach((ds) => ds.clear());
		}
	}

	/**
	 * Updates the signal configs for the y-axis.
	 * If old signals are no longer present in the new list, then the corresponding plots are removed.
	 * If new signals are present in the new list, then new plots are created.
	 * @param sig_y - The new signal configs for the y-axis.
	 */
	protected update_sig_y(sig_y: SignalConfig[]): void {
		const new_set = new Set(sig_y.map((sig) => sig.get_id()));
		const old_set = new Set(this.options.sig_y.map((sig) => sig.get_id()));

		const new_list = sig_y.filter((sig) => new_set.has(sig.get_id()));
		const old_list = this.options.sig_y.filter((sig) => old_set.has(sig.get_id()));

		old_list.forEach((sig, at) => {
			if (!new_set.has(sig.get_id())) {
				this.remove_renderable(at);
			}
		});

		new_list.forEach((sig) => {
			if (!old_set.has(sig.get_id())) {
				this.add_plot();
			}
		});

		this.options.sig_y = new_list;
    }

	/**
	 * Access the data with the given signal config and throws errors.
	 * @param data - The data to access
	 * @param sig - The signal config to access
	 * @returns data[sig.sig_key][sig.sig_idx]
	 */
	protected check_and_fetch(data: ArrayDict, sig: SignalConfig | undefined): NumberArray {
		if (sig === undefined) return [];
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

	protected remove_renderable(at: number): void {
		this.surface.renderableSeries.remove(this.renderable_series[at]);
		this.renderable_series[at]?.delete();
		this.renderable_series.splice(at, 1);

		this.data_series[at]?.delete();
		this.data_series.splice(at, 1);
	}


	/**
	 * A function that specifies how to create the renderable series, dataseries etc. for each subclass.
	 */
	protected abstract add_renderable(): void;

	/**
	 * Calls each update option functions.
	 * @param options - The new plot options
	 */
	public abstract update_all_options(options: PlotOptions): void;
}
